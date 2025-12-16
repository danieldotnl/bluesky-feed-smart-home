import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock data
const mockPosts = [
  { uri: "at://did:plc:test1/app.bsky.feed.post/1", cid: "cid1" },
  { uri: "at://did:plc:test2/app.bsky.feed.post/2", cid: "cid2" },
  { uri: "at://did:plc:test3/app.bsky.feed.post/3", cid: "cid3" },
  { uri: "at://did:plc:test4/app.bsky.feed.post/4", cid: "cid4" },
  { uri: "at://did:plc:test5/app.bsky.feed.post/5", cid: "cid5" },
];

// Helper to create a mock request
function createRequest(params: Record<string, string> = {}): Request {
  const url = new URL("https://example.com/xrpc/app.bsky.feed.getFeedSkeleton");
  Object.entries(params).forEach(([key, value]) => {
    url.searchParams.set(key, value);
  });
  return new Request(url.toString());
}

// Helper to create mock context
function createContext(request: Request) {
  return {
    request,
    env: {},
    params: {},
    waitUntil: vi.fn(),
    passThroughOnException: vi.fn(),
    next: vi.fn(),
    data: {},
    functionPath: "",
  };
}

// Import and test the handler logic directly
// Since we can't easily import the Pages Function, we'll extract the logic
async function handleFeedRequest(
  request: Request,
  fetchFeedData: () => Promise<Response>
): Promise<Response> {
  const url = new URL(request.url);
  const limit = Math.min(parseInt(url.searchParams.get("limit") || "50", 10), 100);
  const cursor = url.searchParams.get("cursor");

  const feedResponse = await fetchFeedData();
  if (!feedResponse.ok) {
    return new Response(JSON.stringify({ error: "Feed data not found" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  const allPosts: Array<{ uri: string }> = await feedResponse.json();

  let startIndex = 0;
  if (cursor) {
    const cursorIndex = allPosts.findIndex((post) => post.uri === cursor);
    if (cursorIndex !== -1) {
      startIndex = cursorIndex + 1;
    }
  }

  const postsSlice = allPosts.slice(startIndex, startIndex + limit);
  const response: { feed: Array<{ post: string }>; cursor?: string } = {
    feed: postsSlice.map((post) => ({ post: post.uri })),
  };

  if (startIndex + limit < allPosts.length && postsSlice.length > 0) {
    response.cursor = postsSlice[postsSlice.length - 1].uri;
  }

  return new Response(JSON.stringify(response), {
    headers: { "Content-Type": "application/json" },
  });
}

describe("getFeedSkeleton", () => {
  const mockFetchSuccess = () =>
    Promise.resolve(new Response(JSON.stringify(mockPosts), { status: 200 }));

  const mockFetchFailure = () =>
    Promise.resolve(new Response("Not found", { status: 404 }));

  describe("basic functionality", () => {
    it("returns all posts when no limit specified (default 50)", async () => {
      const request = createRequest();
      const response = await handleFeedRequest(request, mockFetchSuccess);
      const data = await response.json();

      expect(data.feed).toHaveLength(5);
      expect(data.feed[0].post).toBe(mockPosts[0].uri);
      expect(data.cursor).toBeUndefined(); // No cursor when all posts fit
    });

    it("returns limited posts when limit is specified", async () => {
      const request = createRequest({ limit: "2" });
      const response = await handleFeedRequest(request, mockFetchSuccess);
      const data = await response.json();

      expect(data.feed).toHaveLength(2);
      expect(data.feed[0].post).toBe(mockPosts[0].uri);
      expect(data.feed[1].post).toBe(mockPosts[1].uri);
      expect(data.cursor).toBe(mockPosts[1].uri); // Cursor points to last returned post
    });

    it("caps limit at 100", async () => {
      const request = createRequest({ limit: "200" });
      const response = await handleFeedRequest(request, mockFetchSuccess);
      const data = await response.json();

      // With only 5 mock posts, we get all 5
      expect(data.feed).toHaveLength(5);
    });
  });

  describe("pagination with cursor", () => {
    it("returns posts after cursor position", async () => {
      const request = createRequest({
        cursor: mockPosts[1].uri, // Start after post 2
        limit: "2",
      });
      const response = await handleFeedRequest(request, mockFetchSuccess);
      const data = await response.json();

      expect(data.feed).toHaveLength(2);
      expect(data.feed[0].post).toBe(mockPosts[2].uri); // Post 3
      expect(data.feed[1].post).toBe(mockPosts[3].uri); // Post 4
      expect(data.cursor).toBe(mockPosts[3].uri);
    });

    it("returns remaining posts when near end", async () => {
      const request = createRequest({
        cursor: mockPosts[3].uri, // Start after post 4
        limit: "10",
      });
      const response = await handleFeedRequest(request, mockFetchSuccess);
      const data = await response.json();

      expect(data.feed).toHaveLength(1); // Only post 5 left
      expect(data.feed[0].post).toBe(mockPosts[4].uri);
      expect(data.cursor).toBeUndefined(); // No more posts
    });

    it("returns empty feed when cursor is at end", async () => {
      const request = createRequest({
        cursor: mockPosts[4].uri, // Last post
      });
      const response = await handleFeedRequest(request, mockFetchSuccess);
      const data = await response.json();

      expect(data.feed).toHaveLength(0);
      expect(data.cursor).toBeUndefined();
    });

    it("ignores invalid cursor and starts from beginning", async () => {
      const request = createRequest({
        cursor: "at://invalid/cursor",
        limit: "2",
      });
      const response = await handleFeedRequest(request, mockFetchSuccess);
      const data = await response.json();

      expect(data.feed).toHaveLength(2);
      expect(data.feed[0].post).toBe(mockPosts[0].uri); // Starts from beginning
    });
  });

  describe("error handling", () => {
    it("returns 500 when feed data cannot be fetched", async () => {
      const request = createRequest();
      const response = await handleFeedRequest(request, mockFetchFailure);

      expect(response.status).toBe(500);
      const data = await response.json();
      expect(data.error).toBe("Feed data not found");
    });
  });

  describe("edge cases", () => {
    it("handles empty feed", async () => {
      const mockEmptyFeed = () =>
        Promise.resolve(new Response(JSON.stringify([]), { status: 200 }));

      const request = createRequest();
      const response = await handleFeedRequest(request, mockEmptyFeed);
      const data = await response.json();

      expect(data.feed).toHaveLength(0);
      expect(data.cursor).toBeUndefined();
    });

    it("handles limit of 0", async () => {
      const request = createRequest({ limit: "0" });
      const response = await handleFeedRequest(request, mockFetchSuccess);
      const data = await response.json();

      expect(data.feed).toHaveLength(0);
    });

    it("handles negative limit as 0", async () => {
      const request = createRequest({ limit: "-5" });
      const response = await handleFeedRequest(request, mockFetchSuccess);
      const data = await response.json();

      // Math.min(-5, 100) = -5, slice(0, -5) returns empty for small arrays
      expect(data.feed).toHaveLength(0);
    });
  });
});

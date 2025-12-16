// Cloudflare Pages Function to handle feed skeleton requests with pagination
// This reads the static feed data and returns paginated responses

export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);

  // Parse query parameters
  const limit = Math.min(parseInt(url.searchParams.get("limit") || "50", 10), 100);
  const cursor = url.searchParams.get("cursor");

  // Fetch the static feed data
  const feedDataUrl = new URL("/data/feed.json", url.origin);
  const feedResponse = await fetch(feedDataUrl);

  if (!feedResponse.ok) {
    return new Response(JSON.stringify({ error: "Feed data not found" }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }

  const allPosts = await feedResponse.json();

  // Find starting position based on cursor
  let startIndex = 0;
  if (cursor) {
    const cursorIndex = allPosts.findIndex((post) => post.uri === cursor);
    if (cursorIndex !== -1) {
      startIndex = cursorIndex + 1; // Start after the cursor post
    }
  }

  // Slice the posts
  const postsSlice = allPosts.slice(startIndex, startIndex + limit);

  // Build response
  const feed = postsSlice.map((post) => ({ post: post.uri }));

  // Set cursor if there are more posts
  const response = { feed };
  if (startIndex + limit < allPosts.length) {
    // Use the last post's URI as cursor
    response.cursor = postsSlice[postsSlice.length - 1].uri;
  }

  return new Response(JSON.stringify(response), {
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Cache-Control": "public, max-age=300, s-maxage=300",
    },
  });
}

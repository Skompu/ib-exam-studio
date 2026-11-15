export default {
  async fetch(request, env) {
    const assets = env.ASSETS;
    if (!assets || typeof assets.fetch !== "function") {
      return new Response("IB Exam Studio is unavailable.", {
        status: 503,
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
    }

    const served = await assets.fetch(request);
    if (served.status !== 404) return served;

    const url = new URL(request.url);
    url.pathname = "/index.html";
    return assets.fetch(new Request(url, request));
  },
};

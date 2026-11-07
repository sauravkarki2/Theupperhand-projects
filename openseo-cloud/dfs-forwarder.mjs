// Cloud sessions only: workerd ignores HTTPS_PROXY, so the app sends DataForSEO
// calls to this plain-HTTP localhost forwarder, which relays them to
// https://api.dataforseo.com through Node fetch (run with NODE_USE_ENV_PROXY=1).
// The proxy adds the saved DataForSEO login to each request.
import http from "node:http";
const PORT = Number(process.env.DFS_FORWARDER_PORT || 8789);
http.createServer(async (req, res) => {
  const chunks = [];
  for await (const c of req) chunks.push(c);
  const headers = { ...req.headers };
  delete headers.host; delete headers.connection; delete headers["content-length"]; delete headers["accept-encoding"];
  try {
    const r = await fetch("https://api.dataforseo.com" + req.url, {
      method: req.method, headers, body: chunks.length ? Buffer.concat(chunks) : undefined,
    });
    const body = Buffer.from(await r.arrayBuffer());
    const out = {}; r.headers.forEach((v, k) => { if (!["content-encoding","content-length","transfer-encoding","connection"].includes(k)) out[k] = v; });
    res.writeHead(r.status, out); res.end(body);
    console.log(new Date().toISOString(), req.method, req.url, r.status);
  } catch (e) {
    console.log("forward error", req.url, e.cause?.code || e.message);
    res.writeHead(502); res.end("forwarder error");
  }
}).listen(PORT, "127.0.0.1", () => console.log("dfs-forwarder on", PORT));

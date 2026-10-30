/**
 * Cloudflare Worker Reverse Proxy & Edge Cache cho HK Student Hub (THPT Hương Khê)
 * 
 * Tính năng:
 * - Chuyển tiếp an toàn mọi yêu cầu HTTP/HTTPS về Origin Backend Django.
 * - Cache tệp tĩnh (/static/*, font, ảnh, css, js) tại 300+ Edge Data Centers của Cloudflare,
 *   giúp giảm 90%+ tải cho máy chủ origin và tăng tốc độ tải trang tối đa.
 * - Giữ nguyên toàn bộ Cookie phiên (Session), CSRF Tokens và Headers bảo mật.
 * - Truyền kèm header CF-Connecting-IP để backend ghi nhận đúng IP học sinh trong Nhật ký kiểm toán.
 */

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const originBase = (env.ORIGIN_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

    // 1. Kiểm tra yêu cầu tệp tĩnh để tối ưu Edge Cache
    const isStaticAsset = url.pathname.startsWith('/static/') ||
                          url.pathname.startsWith('/media/') ||
                          url.pathname.match(/\.(css|js|woff2?|ttf|eot|svg|png|jpe?g|webp|ico)$/i);

    // 2. Tạo request chuyển tiếp về Origin
    const targetUrl = new URL(url.pathname + url.search, originBase);
    const newHeaders = new Headers(request.headers);

    // Bổ sung header Cloudflare Zero-Trust
    newHeaders.set('X-Forwarded-Host', url.host);
    newHeaders.set('X-Forwarded-Proto', url.protocol.replace(':', ''));
    if (request.headers.get('cf-connecting-ip')) {
      newHeaders.set('X-Real-IP', request.headers.get('cf-connecting-ip'));
    }

    const modifiedRequest = new Request(targetUrl.toString(), {
      method: request.method,
      headers: newHeaders,
      body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
      redirect: 'manual', // Cho phép backend xử lý 302 redirect chuẩn xác
    });

    // 3. Nếu là tệp tĩnh, sử dụng Cloudflare Edge Cache API
    if (isStaticAsset && request.method === 'GET') {
      const cache = caches.default;
      let cachedResponse = await cache.match(request);
      if (cachedResponse) {
        return cachedResponse;
      }

      const originResponse = await fetch(modifiedRequest);
      if (originResponse.status === 200) {
        const responseToCache = new Response(originResponse.body, originResponse);
        const maxAge = env.CACHE_STATIC_SECONDS || "86400";
        responseToCache.headers.set('Cache-Control', `public, max-age=${maxAge}, stale-while-revalidate=600`);
        ctx.waitUntil(cache.put(request, responseToCache.clone()));
        return responseToCache;
      }
      return originResponse;
    }

    // 4. Các yêu cầu động (API, Auth, Dashboard, Home): Chuyển tiếp trực tiếp không cache
    const originResponse = await fetch(modifiedRequest);
    const responseHeaders = new Headers(originResponse.headers);

    // Chuyển hướng Location nếu backend trả về URL nội bộ
    const location = responseHeaders.get('Location');
    if (location && location.startsWith(originBase)) {
      responseHeaders.set('Location', location.replace(originBase, url.origin));
    }

    return new Response(originResponse.body, {
      status: originResponse.status,
      statusText: originResponse.statusText,
      headers: responseHeaders,
    });
  }
};

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('taxos_access_token')?.value;

  // Protect /org and /admin routes
  if (
    request.nextUrl.pathname.startsWith('/org') ||
    request.nextUrl.pathname.startsWith('/admin') ||
    request.nextUrl.pathname.startsWith('/analytics')
  ) {
    if (!token) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/org/:path*', '/admin/:path*', '/analytics/:path*'],
};

"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { useEffect } from "react";

export default function GoogleAnalytics() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    const url = pathname + (searchParams?.toString() ? `?${searchParams}` : "");

    if (typeof window.gtag === "function") {
      window.gtag("config", "G-VF0WRFHDZT", {
        page_path: url,
      });
    }
  }, [pathname, searchParams]);

  return null;
}

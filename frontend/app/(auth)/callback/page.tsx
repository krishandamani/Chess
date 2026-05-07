"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getSupabaseBrowserClient } from "@/lib/supabase";

export default function CallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const supabase = getSupabaseBrowserClient();

    supabase.auth.onAuthStateChange((event, session) => {
      if (event === "SIGNED_IN" && session) {
        router.replace("/onboarding");
      } else if (event === "TOKEN_REFRESHED" && session) {
        router.replace("/dashboard");
      }
    });

    // Handle hash fragment from magic link
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        router.replace("/dashboard");
      }
    });
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-slate-500 text-sm">Signing you in…</p>
    </div>
  );
}

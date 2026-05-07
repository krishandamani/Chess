import { redirect } from "next/navigation";
import { getSupabaseServerClient } from "@/lib/supabase-server";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const supabase = await getSupabaseServerClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    redirect("/sign-in");
  }

  return <>{children}</>;
}

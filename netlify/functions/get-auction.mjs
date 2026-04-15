import { createClient } from "@supabase/supabase-js";

export default async (request) => {
  try {
    const url = new URL(request.url);
    const slug = url.searchParams.get("slug");

    if (!slug) {
      return new Response(JSON.stringify({ error: "slug fehlt" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }

    const supabase = createClient(
      process.env.SUPABASE_URL,
      process.env.SUPABASE_SERVICE_ROLE_KEY
    );

    const { data: auction, error: auctionError } = await supabase
      .from("auctions")
      .select("*")
      .eq("artwork_slug", slug)
      .single();

    if (auctionError || !auction) {
      return new Response(JSON.stringify({ error: "Auktion nicht gefunden" }), {
        status: 404,
        headers: { "Content-Type": "application/json" }
      });
    }

    const { data: bids, error: bidsError } = await supabase
      .from("bids")
      .select("bidder_name, amount, created_at")
      .eq("auction_id", auction.id)
      .order("amount", { ascending: false })
      .order("created_at", { ascending: false })
      .limit(20);

    if (bidsError) {
      return new Response(JSON.stringify({ error: "Gebote konnten nicht geladen werden" }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }

    return new Response(JSON.stringify({ auction, bids }), {
      status: 200,
      headers: { "Content-Type": "application/json" }
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: "Serverfehler" }), {
      status: 500,
      headers: { "Content-Type": "application/json" }
    });
  }
};
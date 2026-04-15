import { createClient } from "@supabase/supabase-js";

export default async (request) => {
  if (request.method !== "POST") {
    return new Response(JSON.stringify({ error: "Methode nicht erlaubt" }), {
      status: 405,
      headers: { "Content-Type": "application/json" }
    });
  }

  try {
    const body = await request.json();
    const slug = String(body.slug || "").trim();
    const name = String(body.name || "").trim();
    const email = String(body.email || "").trim();
    const amount = Number(body.amount || 0);

    if (!slug || !name || !email || !Number.isFinite(amount) || amount <= 0) {
      return new Response(JSON.stringify({ error: "Ungültige Eingaben" }), {
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

    if (!auction.is_active) {
      return new Response(JSON.stringify({ error: "Auktion ist nicht aktiv" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }

    const endTime = new Date(auction.end_time).getTime();
    if (Date.now() >= endTime) {
      return new Response(JSON.stringify({ error: "Auktion ist beendet" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }

    if (amount <= Number(auction.current_bid)) {
      return new Response(JSON.stringify({ error: "Gebot muss höher als das aktuelle Höchstgebot sein" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }

    const { error: insertError } = await supabase
      .from("bids")
      .insert({
        auction_id: auction.id,
        bidder_name: name,
        bidder_email: email,
        amount
      });

    if (insertError) {
      return new Response(JSON.stringify({ error: "Gebot konnte nicht gespeichert werden" }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }

    const { error: updateError } = await supabase
      .from("auctions")
      .update({ current_bid: amount })
      .eq("id", auction.id);

    if (updateError) {
      return new Response(JSON.stringify({ error: "Höchstgebot konnte nicht aktualisiert werden" }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }

    return new Response(JSON.stringify({
      success: true,
      message: "Gebot gespeichert",
      current_bid: amount
    }), {
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
"use client";

import { useCallback, useEffect, useState } from "react";
import { TicketDetail } from "@/components/TicketDetail";
import { TicketList } from "@/components/TicketList";
import { getTickets } from "@/lib/api";
import type { Ticket } from "@/types";

export function TicketDashboard() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadTickets = useCallback(async (signal?: AbortSignal) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await getTickets(signal);
      setTickets(data);
      setSelectedTicketId((current) =>
        current && data.some((ticket) => ticket.id === current) ? current : (data[0]?.id ?? null),
      );
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") return;
      setErrorMessage(error instanceof Error ? error.message : "Could not load tickets.");
    } finally {
      if (!signal?.aborted) setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void loadTickets(controller.signal);
    return () => controller.abort();
  }, [loadTickets]);

  const selectedTicket = tickets.find((ticket) => ticket.id === selectedTicketId) ?? null;

  return (
    <>
      <header className="masthead">
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true">TF</span>
          <div>
            <p className="eyebrow">Support operations / Desk 01</p>
            <h1>TriageForge</h1>
          </div>
        </div>
        <div className="masthead-status"><span className="live-dot" /> Support desk</div>
      </header>

      <main className="dashboard-shell">
        <section className="page-intro" aria-labelledby="page-title">
          <div>
            <p className="eyebrow">Customer support / Queue overview</p>
            <h2 id="page-title">Ticket desk</h2>
            <p className="intro-copy">Review incoming customer requests and their current status.</p>
          </div>
          <button
            type="button"
            className="refresh-button"
            onClick={() => void loadTickets()}
            disabled={isLoading}
          >
            {isLoading ? "Loading tickets" : "Refresh queue"}
          </button>
        </section>

        {errorMessage ? (
          <section className="notice notice-error" role="alert">
            <div>
              <h2>Ticket service unavailable</h2>
              <p>{errorMessage}</p>
              <p className="notice-hint">Check that the backend is running, then retry.</p>
            </div>
            <button type="button" className="retry-button" onClick={() => void loadTickets()}>
              Retry
            </button>
          </section>
        ) : isLoading && tickets.length === 0 ? (
          <div className="loading-panel" role="status" aria-live="polite">
            <span className="loading-indicator" aria-hidden="true" />
            <p>Loading ticket queue...</p>
          </div>
        ) : (
          <div className="workspace-grid" aria-busy={isLoading}>
            <TicketList
              tickets={tickets}
              selectedTicketId={selectedTicket?.id ?? null}
              onSelect={setSelectedTicketId}
            />
            {selectedTicket ? (
              <TicketDetail ticket={selectedTicket} />
            ) : (
              <section className="panel empty-detail" aria-live="polite">
                <p className="eyebrow">No selection</p>
                <h2>Select a ticket to review</h2>
                <p>Choose a ticket from the queue to see its message and metadata.</p>
              </section>
            )}
          </div>
        )}

        <footer className="page-footer">
          <span>SupportAgent Desk</span>
          <span>Ticket data is served by the backend API.</span>
        </footer>
      </main>
    </>
  );
}

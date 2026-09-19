"use client";
// =============================================================================
// useTransactions — Supabase-backed Transactions Hook
// =============================================================================

import { useState, useEffect, useCallback, useRef } from "react";
import { fetchTransactions } from "@/lib/api";
import type { TransactionRead, PaginationMeta, TransactionFilterParams } from "@/lib/types";

interface UseTransactionsResult {
  transactions: TransactionRead[];
  pagination: PaginationMeta | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
  isLive: boolean;
}

export function useTransactions(params?: TransactionFilterParams & { page?: number; page_size?: number }): UseTransactionsResult {
  const [transactions, setTransactions] = useState<TransactionRead[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isLive, setIsLive] = useState(false);
  const isMounted = useRef(true);

  const paramsString = JSON.stringify(params);

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    setError(null);
    try {
      const currentParams = paramsString ? JSON.parse(paramsString) : undefined;
      const res = await fetchTransactions(currentParams);
      if (!isMounted.current) return;
      setTransactions(res.data || []);
      setPagination(res.pagination);
      setIsLive(!res.message.includes("cached") && !res.message.includes("Mock"));
    } catch (err) {
      if (!isMounted.current) return;
      setError(err instanceof Error ? err.message : "Failed to load transactions");
    } finally {
      if (!isMounted.current) return;
      if (!silent) setLoading(false);
    }
  }, [paramsString]);

  useEffect(() => {
    isMounted.current = true;
    load();
    return () => {
      isMounted.current = false;
    };
  }, [load]);

  return { transactions, pagination, loading, error, refetch: () => load(false), isLive };
}

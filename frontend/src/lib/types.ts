// TypeScript types for WhatsApp Unwrapped frontend data
// These types match the output of backend/output/frontend_export.py

export interface UnwrappedData {
  id: string;
  chatName: string;
  generatedAt: string;
  overview: Overview;
  leaderboard: LeaderboardEntry[];
  peakTimes: PeakTimes;
  funFacts: string[];
  awards: Award[];
  highlights?: Highlights | null;
}

export interface Overview {
  totalMessages: number;
  totalDays: number;
  participantCount: number;
  dateRange: {
    start: string;
    end: string;
  };
}

export interface LeaderboardEntry {
  name: string;
  messages: number;
  percentage: number;
}

export interface PeakTimes {
  busiestHour: number;
  busiestHourFormatted: string;
  busiestDay: string;
}

export interface Award {
  title: string;
  recipient: string;
  evidence: string;
  quip: string;
}

export interface Highlights {
  notableQuotes?: Quote[];
  insideJokes?: InsideJoke[];
  dynamics?: string[];
  funnyMoments?: string[];
  contradictions?: Contradiction[];
  bestExchanges?: Exchange[];
}

export interface Quote {
  text: string;
  author: string;
  context?: string;  // The witty commentary about the quote
}

export interface InsideJoke {
  reference: string;
  explanation: string;
}

export interface Contradiction {
  person: string;
  says: string;
  does: string;
  punchline?: string;
}

export interface Exchange {
  context: string;
  exchange?: ExchangeMessage[];
  punchline: string;
}

export interface ExchangeMessage {
  sender: string;
  text: string;
}

// Message types for the chat UI
export type MessageSender = "bot" | "user";
export type MessageStatus = "sending" | "sent" | "delivered" | "read";

export interface ChatMessage {
  id: string;
  content: React.ReactNode;
  sender: MessageSender;
  timestamp: string;
  status?: MessageStatus;
  delay?: number;
}

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
  insideJokes?: string[];
  dynamics?: string[];
  funnyMoments?: string[];
  contradictions?: Contradiction[];
  bestExchanges?: Exchange[];
}

export interface Quote {
  text: string;
  author: string;
  context?: string;
}

export interface Contradiction {
  person: string;
  says: string;
  does: string;
}

export interface Exchange {
  context: string;
  punchline: string;
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

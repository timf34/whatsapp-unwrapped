// TypeScript types for WhatsApp Unwrapped frontend data

export interface UnwrappedData {
  id: string;
  chatName: string;
  generatedAt: string;
  overview: Overview;
  leaderboard: LeaderboardEntry[];
  peakTimes: PeakTimes;
  funFacts: string[];
  awards: Award[];
  highlights?: Highlights;
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
  heatmapData?: number[][];
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
  conversationSnippets?: string[];
}

export interface Quote {
  text: string;
  author: string;
  context?: string;
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
  delay?: number; // Delay before showing this message
}

// Content types that can appear in messages
export interface StatCard {
  type: "stat";
  emoji: string;
  label: string;
  value: string | number;
}

export interface LeaderboardCard {
  type: "leaderboard";
  entries: LeaderboardEntry[];
}

export interface AwardMessageContent {
  type: "award";
  award: Award;
}

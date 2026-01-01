"use client";

import ChatBubble from "@/components/ChatBubble";
import ChatHeader from "@/components/ChatHeader";
import DateBadge from "@/components/DateBadge";
import Leaderboard from "@/components/Leaderboard";
import AwardCard from "@/components/AwardCard";
import { StatGrid } from "@/components/StatCard";
import type { UnwrappedData } from "@/lib/types";

// Demo data - in production this would come from a JSON file or API
const demoData: UnwrappedData = {
  id: "fitz-2024-unwrapped",
  chatName: "Fitzwilliam Group Chat",
  generatedAt: "2024-12-31T12:00:00Z",
  overview: {
    totalMessages: 793,
    totalDays: 19,
    participantCount: 18,
    dateRange: { start: "2024-12-01", end: "2024-12-19" },
  },
  leaderboard: [
    { name: "Sam", messages: 234, percentage: 29.5 },
    { name: "Alex", messages: 156, percentage: 19.7 },
    { name: "Tim", messages: 89, percentage: 11.2 },
    { name: "Jordan", messages: 67, percentage: 8.4 },
    { name: "Casey", messages: 54, percentage: 6.8 },
    { name: "Morgan", messages: 48, percentage: 6.0 },
  ],
  peakTimes: {
    busiestHour: 21,
    busiestHourFormatted: "9 PM",
    busiestDay: "Wednesday",
  },
  funFacts: [
    "You've been chatting for 19 days straight!",
    "Longest streak: 14 days in a row!",
    "47 photos and videos shared",
    "12 deleted messages... suspicious",
  ],
  awards: [
    {
      title: "The Voice Note Novelist",
      recipient: "Sarah",
      evidence: "Sent 23 voice notes averaging 2 minutes each",
      quip: "Some say they're still listening...",
    },
    {
      title: "The Ghost",
      recipient: "Mike",
      evidence: "Lurked for 12 days before dropping a single 'lol'",
      quip: "Efficiency at its finest",
    },
    {
      title: "The Early Bird",
      recipient: "Tim",
      evidence: "Sent 34 messages before 7 AM",
      quip: "Either an insomniac or just loves coffee",
    },
  ],
};

export default function Home() {
  const data = demoData;

  return (
    <div className="min-h-screen flex flex-col bg-[#efeae2]">
      <ChatHeader
        chatName={data.chatName}
        participantCount={data.overview.participantCount}
      />

      <main className="flex-1 chat-background chat-scroll overflow-y-auto">
        <div className="max-w-2xl mx-auto px-4 py-6 pb-32">
          {/* Date badge */}
          <DateBadge text="TODAY" />

          {/* Act 1: Welcome */}
          <ChatBubble sender="bot" timestamp="12:00" delay={0}>
            Hey! I&apos;ve been analyzing your <strong>{data.chatName}</strong> 👋
          </ChatBubble>

          <ChatBubble sender="bot" timestamp="12:00" delay={0.2}>
            Ready to see what {data.overview.totalMessages.toLocaleString()} messages
            and {data.overview.totalDays} days of chatting look like?
          </ChatBubble>

          <ChatBubble sender="user" timestamp="12:01" delay={0.4}>
            Yes! Show me everything! 🎉
          </ChatBubble>

          {/* Act 2: Overview Stats */}
          <ChatBubble sender="bot" timestamp="12:01" delay={0.6}>
            Here&apos;s the big picture...
          </ChatBubble>

          <div className="flex justify-start mb-3">
            <div className="max-w-[90%] md:max-w-[80%]">
              <StatGrid
                stats={[
                  { emoji: "💬", value: data.overview.totalMessages.toLocaleString(), label: "messages" },
                  { emoji: "📅", value: data.overview.totalDays, label: "days" },
                  { emoji: "👥", value: data.overview.participantCount, label: "people" },
                  { emoji: "🔥", value: Math.round(data.overview.totalMessages / data.overview.totalDays), label: "msgs/day" },
                ]}
                delay={0.8}
              />
            </div>
          </div>

          <ChatBubble sender="bot" timestamp="12:01" delay={1.2}>
            That&apos;s {Math.round(data.overview.totalMessages / data.overview.totalDays)} messages per day on average! 🔥
          </ChatBubble>

          {/* Act 3: Leaderboard */}
          <ChatBubble sender="bot" timestamp="12:02" delay={1.4}>
            And the chattiest award goes to...
          </ChatBubble>

          <div className="flex justify-start mb-3">
            <Leaderboard entries={data.leaderboard} delay={1.6} />
          </div>

          <ChatBubble sender="bot" timestamp="12:02" delay={2.2}>
            {data.leaderboard[0].name} really does love talking, huh? 😂
          </ChatBubble>

          <ChatBubble sender="user" timestamp="12:02" delay={2.4}>
            Haha no surprise there!
          </ChatBubble>

          {/* Act 4: Peak Times */}
          <ChatBubble sender="bot" timestamp="12:03" delay={2.6}>
            When do you chat the most?
          </ChatBubble>

          <ChatBubble sender="bot" timestamp="12:03" delay={2.8}>
            <div className="text-center py-2">
              <div className="text-3xl mb-1">🕘</div>
              <div className="font-bold text-lg">{data.peakTimes.busiestHourFormatted}</div>
              <div className="text-sm text-gray-500">on {data.peakTimes.busiestDay}s</div>
            </div>
          </ChatBubble>

          <ChatBubble sender="bot" timestamp="12:03" delay={3.0}>
            Looks like {data.peakTimes.busiestHourFormatted} on {data.peakTimes.busiestDay}s is peak chaos time 💀
          </ChatBubble>

          {/* Act 5: Fun Facts */}
          <ChatBubble sender="bot" timestamp="12:04" delay={3.2}>
            Want some fun facts? 🎲
          </ChatBubble>

          <ChatBubble sender="user" timestamp="12:04" delay={3.4}>
            Hit me!
          </ChatBubble>

          {data.funFacts.map((fact, i) => (
            <ChatBubble key={i} sender="bot" timestamp="12:04" delay={3.6 + i * 0.3}>
              {fact}
            </ChatBubble>
          ))}

          {/* Act 6: Awards */}
          <ChatBubble sender="bot" timestamp="12:05" delay={5.0}>
            Now for the awards... 🏆
          </ChatBubble>

          {data.awards.map((award, i) => (
            <AwardCard key={i} award={award} delay={5.2 + i * 0.4} />
          ))}

          {/* Act 7: Sign-off */}
          <ChatBubble sender="bot" timestamp="12:06" delay={6.8}>
            That&apos;s your Unwrapped! 🎉
          </ChatBubble>

          <ChatBubble sender="bot" timestamp="12:06" delay={7.0}>
            Share it with the group and see if they agree with the awards 😏
          </ChatBubble>

          <ChatBubble sender="user" timestamp="12:06" delay={7.2}>
            This was amazing, thanks! 🙌
          </ChatBubble>

          <ChatBubble sender="bot" timestamp="12:06" delay={7.4}>
            See you next year! 👋
          </ChatBubble>

          {/* Scroll indicator at bottom */}
          <div className="text-center py-8 text-gray-400 text-sm">
            ✨ End of Unwrapped ✨
          </div>
        </div>
      </main>
    </div>
  );
}

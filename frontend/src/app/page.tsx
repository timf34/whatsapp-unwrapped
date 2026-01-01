"use client";

import { useEffect, useState } from "react";
import ChatBubble from "@/components/ChatBubble";
import ChatHeader from "@/components/ChatHeader";
import DateBadge from "@/components/DateBadge";
import Leaderboard from "@/components/Leaderboard";
import AwardCard from "@/components/AwardCard";
import { StatGrid } from "@/components/StatCard";
import type { UnwrappedData } from "@/lib/types";

// Demo data used when no JSON file is available
const demoData: UnwrappedData = {
  id: "demo",
  chatName: "Demo Group Chat",
  generatedAt: new Date().toISOString(),
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
  highlights: null,
};

export default function Home() {
  const [data, setData] = useState<UnwrappedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        // Try to load from unwrapped.json first
        const response = await fetch("/data/unwrapped.json");
        if (response.ok) {
          const jsonData = await response.json();
          setData(jsonData);
        } else {
          // Fall back to demo data
          console.log("No unwrapped.json found, using demo data");
          setData(demoData);
        }
      } catch (err) {
        console.log("Error loading data, using demo:", err);
        setData(demoData);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#e4dcd4]">
        <div className="text-[#667781] text-lg">Loading your Unwrapped...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#e4dcd4]">
        <div className="text-red-500">Failed to load data</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <ChatHeader
        chatName={data.chatName}
        participantCount={data.overview.participantCount}
      />

      {/* Chat area with background */}
      <div className="flex-1 relative bg-[#e4dcd4]">
        {/* Background pattern overlay */}
        <div
          className="absolute inset-0 opacity-[0.06]"
          style={{
            backgroundImage: "url('/assets/images/bg-chat-room.png')",
            backgroundRepeat: "repeat",
          }}
        />

        {/* Messages container */}
        <div className="relative z-10 overflow-y-auto h-[calc(100vh-60px)] py-4">
          {/* Date badge */}
          <DateBadge text="YOUR UNWRAPPED" />

          {/* Act 1: Welcome */}
          <ChatBubble sender="bot" timestamp="12:00" delay={0}>
            Hey! I&apos;ve been analyzing your <strong>{data.chatName}</strong> 👋
          </ChatBubble>

          <ChatBubble sender="bot" timestamp="12:00" delay={0.15} showTail={false}>
            Ready to see what {data.overview.totalMessages.toLocaleString()} messages
            and {data.overview.totalDays} days of chatting look like?
          </ChatBubble>

          <ChatBubble sender="user" timestamp="12:01" delay={0.3}>
            Yes! Show me everything! 🎉
          </ChatBubble>

          {/* Act 2: Overview Stats */}
          <ChatBubble sender="bot" timestamp="12:01" delay={0.45}>
            Here&apos;s the big picture...
          </ChatBubble>

          <div className="flex justify-start mb-2 px-[5%] md:px-[63px]">
            <div className="max-w-[85%] md:max-w-[65%]">
              <StatGrid
                stats={[
                  { emoji: "💬", value: data.overview.totalMessages.toLocaleString(), label: "messages" },
                  { emoji: "📅", value: data.overview.totalDays, label: "days" },
                  { emoji: "👥", value: data.overview.participantCount, label: "people" },
                  { emoji: "🔥", value: Math.round(data.overview.totalMessages / data.overview.totalDays), label: "msgs/day" },
                ]}
                delay={0.6}
              />
            </div>
          </div>

          <ChatBubble sender="bot" timestamp="12:01" delay={0.9} showTail={false}>
            That&apos;s {Math.round(data.overview.totalMessages / data.overview.totalDays)} messages per day on average! 🔥
          </ChatBubble>

          {/* Act 3: Leaderboard */}
          <ChatBubble sender="bot" timestamp="12:02" delay={1.05}>
            And the chattiest award goes to...
          </ChatBubble>

          <div className="flex justify-start mb-2 px-[5%] md:px-[63px]">
            <Leaderboard entries={data.leaderboard} delay={1.2} />
          </div>

          <ChatBubble sender="bot" timestamp="12:02" delay={1.8} showTail={false}>
            {data.leaderboard[0]?.name || "Someone"} really does love talking, huh? 😂
          </ChatBubble>

          <ChatBubble sender="user" timestamp="12:02" delay={1.95}>
            Haha no surprise there!
          </ChatBubble>

          {/* Act 4: Peak Times */}
          <ChatBubble sender="bot" timestamp="12:03" delay={2.1}>
            When do you chat the most?
          </ChatBubble>

          <ChatBubble sender="bot" timestamp="12:03" delay={2.25} showTail={false}>
            <div className="text-center py-2">
              <div className="text-3xl mb-1">🕘</div>
              <div className="font-semibold text-lg">{data.peakTimes.busiestHourFormatted}</div>
              <div className="text-sm text-[#667781]">on {data.peakTimes.busiestDay}s</div>
            </div>
          </ChatBubble>

          <ChatBubble sender="bot" timestamp="12:03" delay={2.4} showTail={false}>
            Looks like {data.peakTimes.busiestHourFormatted} on {data.peakTimes.busiestDay}s is peak chaos time 💀
          </ChatBubble>

          {/* Act 5: Fun Facts */}
          {data.funFacts.length > 0 && (
            <>
              <ChatBubble sender="bot" timestamp="12:04" delay={2.55}>
                Want some fun facts? 🎲
              </ChatBubble>

              <ChatBubble sender="user" timestamp="12:04" delay={2.7}>
                Hit me!
              </ChatBubble>

              {data.funFacts.slice(0, 6).map((fact, i) => (
                <ChatBubble
                  key={i}
                  sender="bot"
                  timestamp="12:04"
                  delay={2.85 + i * 0.15}
                  showTail={i === 0}
                >
                  {fact}
                </ChatBubble>
              ))}
            </>
          )}

          {/* Act 6: Awards */}
          {data.awards.length > 0 && (
            <>
              <ChatBubble sender="bot" timestamp="12:05" delay={3.6}>
                Now for the awards... 🏆
              </ChatBubble>

              <div className="px-[5%] md:px-[63px]">
                {data.awards.map((award, i) => (
                  <AwardCard key={i} award={award} delay={3.75 + i * 0.3} />
                ))}
              </div>
            </>
          )}

          {/* Act 7: Sign-off */}
          <ChatBubble sender="bot" timestamp="12:06" delay={3.6 + data.awards.length * 0.3 + 0.3}>
            That&apos;s your Unwrapped! 🎉
          </ChatBubble>

          <ChatBubble sender="bot" timestamp="12:06" delay={3.6 + data.awards.length * 0.3 + 0.45} showTail={false}>
            Share it with the group and see if they agree with the awards 😏
          </ChatBubble>

          <ChatBubble sender="user" timestamp="12:06" delay={3.6 + data.awards.length * 0.3 + 0.6}>
            This was amazing, thanks! 🙌
          </ChatBubble>

          <ChatBubble sender="bot" timestamp="12:06" delay={3.6 + data.awards.length * 0.3 + 0.75}>
            See you next year! 👋
          </ChatBubble>

          {/* Bottom padding for scroll */}
          <div className="h-8" />
        </div>
      </div>
    </div>
  );
}

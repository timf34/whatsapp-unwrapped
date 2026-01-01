"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import type { LeaderboardEntry } from "@/lib/types";

interface LeaderboardProps {
  entries: LeaderboardEntry[];
  delay?: number;
}

const medals = ["🥇", "🥈", "🥉"];
const colors = [
  "from-amber-400 to-yellow-500",
  "from-gray-300 to-slate-400",
  "from-orange-400 to-amber-600",
];

export default function Leaderboard({ entries, delay = 0 }: LeaderboardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  const topThree = entries.slice(0, 3);
  const rest = entries.slice(3, 6);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{
        delay: delay,
        duration: 0.5,
        ease: [0.25, 0.46, 0.45, 0.94],
      }}
      className="bg-white rounded-xl shadow-md overflow-hidden max-w-[95%] md:max-w-[80%]"
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-500 to-teal-500 px-4 py-3">
        <h3 className="font-bold text-white text-sm flex items-center gap-2">
          <span className="text-lg">👑</span>
          Top Chatters
        </h3>
      </div>

      {/* Podium */}
      <div className="p-4 space-y-2">
        {topThree.map((entry, i) => (
          <motion.div
            key={entry.name}
            initial={{ opacity: 0, x: -20 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ delay: delay + 0.2 + i * 0.15, duration: 0.4 }}
            className="flex items-center gap-3"
          >
            <span className="text-2xl">{medals[i]}</span>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-gray-900">{entry.name}</span>
                <span className="text-sm text-gray-500">{entry.messages} msgs</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  className={`h-full bg-gradient-to-r ${colors[i]} rounded-full`}
                  initial={{ width: 0 }}
                  animate={isInView ? { width: `${entry.percentage}%` } : {}}
                  transition={{ delay: delay + 0.4 + i * 0.15, duration: 0.8, ease: "easeOut" }}
                />
              </div>
            </div>
            <span className="text-sm font-medium text-gray-600 w-12 text-right">
              {entry.percentage.toFixed(0)}%
            </span>
          </motion.div>
        ))}

        {/* Rest of entries (smaller) */}
        {rest.length > 0 && (
          <div className="pt-2 mt-2 border-t border-gray-100 space-y-1">
            {rest.map((entry, i) => (
              <motion.div
                key={entry.name}
                initial={{ opacity: 0 }}
                animate={isInView ? { opacity: 1 } : {}}
                transition={{ delay: delay + 0.6 + i * 0.1, duration: 0.3 }}
                className="flex items-center gap-2 text-sm text-gray-600"
              >
                <span className="w-6 text-center">{i + 4}.</span>
                <span className="flex-1">{entry.name}</span>
                <span>{entry.messages}</span>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

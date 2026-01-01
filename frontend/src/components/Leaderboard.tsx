"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import type { LeaderboardEntry } from "@/lib/types";

interface LeaderboardProps {
  entries: LeaderboardEntry[];
  delay?: number;
}

const medals = ["🥇", "🥈", "🥉"];
const barColors = ["bg-[#25d366]", "bg-[#34b7f1]", "bg-[#f6b93b]"];

export default function Leaderboard({ entries, delay = 0 }: LeaderboardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  const topThree = entries.slice(0, 3);
  const rest = entries.slice(3, 6);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{
        delay: delay,
        duration: 0.3,
        ease: "easeOut",
      }}
      className="bg-white rounded-[7.5px] shadow-[0_1px_0.5px_rgba(11,20,26,0.13)] overflow-hidden max-w-full"
    >
      {/* Header */}
      <div className="bg-[#00a884] px-4 py-2">
        <h3 className="font-medium text-white text-[14px] flex items-center gap-2">
          <span>👑</span>
          Top Chatters
        </h3>
      </div>

      {/* Content */}
      <div className="p-3 space-y-3">
        {topThree.map((entry, i) => (
          <motion.div
            key={entry.name}
            initial={{ opacity: 0, x: -20 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ delay: delay + 0.15 + i * 0.1, duration: 0.3 }}
            className="flex items-center gap-2"
          >
            <span className="text-lg w-6">{medals[i]}</span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-[14px] text-[#111b21] truncate">{entry.name}</span>
                <span className="text-[12px] text-[#667781] ml-2 flex-shrink-0">{entry.messages}</span>
              </div>
              <div className="h-[6px] bg-[#f0f2f5] rounded-full overflow-hidden">
                <motion.div
                  className={`h-full ${barColors[i]} rounded-full`}
                  initial={{ width: 0 }}
                  animate={isInView ? { width: `${entry.percentage}%` } : {}}
                  transition={{ delay: delay + 0.3 + i * 0.1, duration: 0.5, ease: "easeOut" }}
                />
              </div>
            </div>
            <span className="text-[12px] font-medium text-[#667781] w-10 text-right">
              {entry.percentage.toFixed(0)}%
            </span>
          </motion.div>
        ))}

        {/* Rest of entries */}
        {rest.length > 0 && (
          <div className="pt-2 border-t border-[#f0f2f5] space-y-1">
            {rest.map((entry, i) => (
              <motion.div
                key={entry.name}
                initial={{ opacity: 0 }}
                animate={isInView ? { opacity: 1 } : {}}
                transition={{ delay: delay + 0.5 + i * 0.05, duration: 0.2 }}
                className="flex items-center gap-2 text-[13px] text-[#667781]"
              >
                <span className="w-6 text-center">{i + 4}.</span>
                <span className="flex-1 truncate">{entry.name}</span>
                <span>{entry.messages}</span>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

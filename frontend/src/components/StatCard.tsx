"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";

interface StatCardProps {
  emoji: string;
  value: string | number;
  label: string;
  delay?: number;
}

export default function StatCard({ emoji, value, label, delay = 0 }: StatCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={isInView ? { opacity: 1, scale: 1 } : {}}
      transition={{
        delay: delay,
        duration: 0.3,
        ease: "easeOut",
      }}
      className="bg-white rounded-lg p-3 text-center shadow-[0_1px_0.5px_rgba(11,20,26,0.13)]"
    >
      <div className="text-2xl mb-1">{emoji}</div>
      <div className="text-xl font-semibold text-[#111b21]">{value}</div>
      <div className="text-xs text-[#667781]">{label}</div>
    </motion.div>
  );
}

interface StatGridProps {
  stats: Array<{ emoji: string; value: string | number; label: string }>;
  delay?: number;
}

export function StatGrid({ stats, delay = 0 }: StatGridProps) {
  return (
    <div className="grid grid-cols-2 gap-2 p-1">
      {stats.map((stat, i) => (
        <StatCard
          key={i}
          emoji={stat.emoji}
          value={stat.value}
          label={stat.label}
          delay={delay + i * 0.08}
        />
      ))}
    </div>
  );
}

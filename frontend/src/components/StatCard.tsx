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
        duration: 0.4,
        ease: [0.25, 0.46, 0.45, 0.94],
      }}
      className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-xl p-4 text-center shadow-sm border border-emerald-100"
    >
      <div className="text-3xl mb-1">{emoji}</div>
      <div className="text-2xl font-bold text-emerald-700">{value}</div>
      <div className="text-sm text-gray-600">{label}</div>
    </motion.div>
  );
}

interface StatGridProps {
  stats: Array<{ emoji: string; value: string | number; label: string }>;
  delay?: number;
}

export function StatGrid({ stats, delay = 0 }: StatGridProps) {
  return (
    <div className="grid grid-cols-2 gap-3 p-1">
      {stats.map((stat, i) => (
        <StatCard
          key={i}
          emoji={stat.emoji}
          value={stat.value}
          label={stat.label}
          delay={delay + i * 0.1}
        />
      ))}
    </div>
  );
}

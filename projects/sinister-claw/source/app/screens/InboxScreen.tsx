// Sinister Claw :: screens/InboxScreen.tsx
// Author: RKOJ-ELENO :: 2026-05-21
// License: AGPL-3.0-or-later
//
// Operator phone-side inbox. Aggregates _shared-memory/inbox/<agent>/*.json
// and _shared-memory/cross-agent/*.md. Read-only on v1 - ack flow stays on
// the operator's PC (PS1 helper / RKOJ Inbox tab). Phone is for "did anything
// land?" awareness while operator is away from the rig.

import React, { useCallback, useEffect, useState } from "react";
import {
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { GlassPanel } from "@/components/GlassPanel";
import { colors, radii, spacing, typography, projectAccents } from "@/theme";
import { getInbox, InboxItem } from "@/api/sanctum";

const POLL_MS = 15000;
const PAGE_LIMIT = 50;

const TAG_COLORS: Record<string, string> = {
  ASK: "#FFD66E",
  ACK: "#6EFFA0",
  PUSHBACK: "#FF6E6E",
  BROADCAST: "#6EE8FF",
  COAUDIT: "#FF6EE8",
  DISCOVERY: "#A06EFF",
  DELEGATE: "#FF8C42",
};

export function InboxScreen() {
  const [items, setItems] = useState<InboxItem[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string | null>(null);
  const [open, setOpen] = useState<InboxItem | null>(null);

  const refresh = useCallback(async () => {
    try {
      const resp = await getInbox(PAGE_LIMIT);
      setItems(resp.items);
      setTotal(resp.total);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_MS);
    return () => clearInterval(id);
  }, [refresh]);

  const tagsPresent = Array.from(new Set(items.map((i) => i.tag).filter(Boolean))).sort();
  const visible = filter ? items.filter((i) => i.tag === filter) : items;

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={[typography.display, { color: colors.purpleBright }]}>
          ◈ INBOX
        </Text>
        <Text style={[typography.caption, { marginBottom: spacing.lg }]}>
          {visible.length} of {total} messages
        </Text>

        {error && (
          <GlassPanel style={{ marginBottom: spacing.md }}>
            <Text style={{ color: colors.red }}>Bridge unreachable: {error}</Text>
          </GlassPanel>
        )}

        {tagsPresent.length > 0 && (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: spacing.md }}>
            <Pressable
              onPress={() => setFilter(null)}
              style={[styles.tagChip, !filter && styles.tagChipActive]}
            >
              <Text style={[styles.tagChipText, !filter && { color: colors.purpleBright }]}>ALL</Text>
            </Pressable>
            {tagsPresent.map((t) => {
              const active = filter === t;
              const accent = TAG_COLORS[t] ?? colors.purpleBright;
              return (
                <Pressable
                  key={t}
                  onPress={() => setFilter(active ? null : t)}
                  style={[
                    styles.tagChip,
                    active && { backgroundColor: accent + "22", borderColor: accent },
                  ]}
                >
                  <Text style={[styles.tagChipText, active && { color: accent }]}>{t}</Text>
                </Pressable>
              );
            })}
          </ScrollView>
        )}

        {visible.map((item) => {
          const accent = projectAccents[item.project_hint] ?? colors.purpleBright;
          const tagColor = TAG_COLORS[item.tag] ?? colors.dim;
          return (
            <Pressable key={item.id} onPress={() => setOpen(item)}>
              <GlassPanel style={{ marginBottom: spacing.sm, borderColor: accent + "33" }}>
                <View style={styles.row}>
                  {item.tag && (
                    <View style={[styles.tagBadge, { borderColor: tagColor }]}>
                      <Text style={[styles.tagBadgeText, { color: tagColor }]}>{item.tag}</Text>
                    </View>
                  )}
                  <Text style={[typography.caption, { color: accent }]}>
                    {item.from} → {item.to}
                  </Text>
                </View>
                <Text style={[typography.body, { marginTop: spacing.xs }]} numberOfLines={2}>
                  {item.subject}
                </Text>
                <Text style={[typography.caption, { marginTop: spacing.xs }]}>
                  {formatAgo(item.ts_utc)} · {item.source}
                </Text>
              </GlassPanel>
            </Pressable>
          );
        })}
      </ScrollView>

      <DetailSheet item={open} onClose={() => setOpen(null)} />
    </SafeAreaView>
  );
}

function DetailSheet({ item, onClose }: { item: InboxItem | null; onClose: () => void }) {
  if (!item) return null;
  const accent = projectAccents[item.project_hint] ?? colors.purpleBright;
  const tagColor = TAG_COLORS[item.tag] ?? colors.dim;
  return (
    <Modal visible animationType="slide" transparent onRequestClose={onClose}>
      <SafeAreaView style={styles.detailContainer}>
        <View style={[styles.detailHeader, { borderColor: accent + "55" }]}>
          <View style={{ flex: 1 }}>
            {item.tag && (
              <View style={[styles.tagBadge, { borderColor: tagColor, alignSelf: "flex-start" }]}>
                <Text style={[styles.tagBadgeText, { color: tagColor }]}>{item.tag}</Text>
              </View>
            )}
            <Text style={[typography.h1, { color: accent, marginTop: spacing.xs }]}>
              {item.from} → {item.to}
            </Text>
            <Text style={[typography.caption, { marginTop: spacing.xs }]}>
              {item.ts_utc} · {item.source}
            </Text>
          </View>
          <Pressable onPress={onClose}>
            <Text style={[typography.h2, { color: colors.dim }]}>CLOSE</Text>
          </Pressable>
        </View>
        <ScrollView contentContainerStyle={{ padding: spacing.md }}>
          <Text style={[typography.title, { marginBottom: spacing.md }]}>{item.subject}</Text>
          <Text style={styles.bodyText}>{item.body}</Text>
          <Text style={[typography.caption, { marginTop: spacing.lg }]}>
            path: {item.body_path}
          </Text>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

function formatAgo(iso: string): string {
  if (!iso) return "";
  const then = Date.parse(iso);
  if (Number.isNaN(then)) return iso;
  const min = Math.floor((Date.now() - then) / 60000);
  if (min < 1) return "just now";
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const d = Math.floor(hr / 24);
  return `${d}d ago`;
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bgDeep },
  scroll: { padding: spacing.lg },
  row: { flexDirection: "row", alignItems: "center" },
  tagChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: colors.borderGlass,
    marginRight: spacing.sm,
  },
  tagChipActive: {
    backgroundColor: colors.purpleSoft,
    borderColor: colors.purpleBright,
  },
  tagChipText: {
    color: colors.soft,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1,
  },
  tagBadge: {
    borderWidth: 1,
    borderRadius: radii.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    marginRight: spacing.sm,
  },
  tagBadgeText: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 1,
  },
  detailContainer: {
    flex: 1,
    backgroundColor: colors.bgDeep,
  },
  detailHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    padding: spacing.md,
    borderBottomWidth: 1,
  },
  bodyText: {
    color: colors.lightPurple,
    fontFamily: "Menlo",
    fontSize: 11,
    lineHeight: 16,
  },
});

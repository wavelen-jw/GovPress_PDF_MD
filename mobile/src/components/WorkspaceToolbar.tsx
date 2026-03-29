import React from "react";
import { Pressable, Text, View } from "react-native";

import { styles } from "../styles";
import type { JobStatus } from "../types";

type Props = {
  currentServer: string;
  isWideLayout: boolean;
  stats: Record<JobStatus, number>;
  onOpenSettings: () => void;
  onPickPdf: () => void;
  onRefresh: () => void;
  onUseCurrentHost?: () => void;
};

export function WorkspaceToolbar({
  currentServer,
  isWideLayout,
  stats,
  onOpenSettings,
  onPickPdf,
  onRefresh,
  onUseCurrentHost,
}: Props) {
  return (
    <View style={[styles.workspaceToolbar, isWideLayout && styles.workspaceToolbarDesktop]}>
      <View style={styles.workspaceToolbarMain}>
        <Text style={styles.workspaceToolbarTitle}>작업 도구</Text>
        <Text style={styles.workspaceToolbarBody}>업로드와 새로고침, 서버 전환을 한 곳에서 처리합니다.</Text>
        <View style={styles.workspaceToolbarActions}>
          <Pressable style={styles.primaryButton} onPress={onPickPdf}>
            <Text style={styles.primaryButtonLabel}>PDF 업로드</Text>
          </Pressable>
          <Pressable style={styles.secondaryButton} onPress={onRefresh}>
            <Text style={styles.secondaryButtonLabel}>목록 새로고침</Text>
          </Pressable>
          <Pressable style={styles.secondaryButton} onPress={onOpenSettings}>
            <Text style={styles.secondaryButtonLabel}>서버 설정</Text>
          </Pressable>
          {onUseCurrentHost ? (
            <Pressable style={styles.secondaryButton} onPress={onUseCurrentHost}>
              <Text style={styles.secondaryButtonLabel}>이 페이지 서버 사용</Text>
            </Pressable>
          ) : null}
        </View>
        <Text style={styles.workspaceToolbarHint}>현재 서버: {currentServer}</Text>
      </View>

      <View style={styles.workspaceToolbarStats}>
        {[
          ["queued", "대기"],
          ["processing", "진행"],
          ["completed", "완료"],
          ["failed", "실패"],
        ].map(([key, label]) => (
          <View key={key} style={styles.workspaceStatCard}>
            <Text style={styles.workspaceStatValue}>{stats[key as JobStatus]}</Text>
            <Text style={styles.workspaceStatLabel}>{label}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

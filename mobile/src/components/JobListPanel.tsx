import React, { startTransition } from "react";
import { Pressable, ScrollView, Text, TextInput, View } from "react-native";

import { STATUS_COPY } from "../constants";
import { styles } from "../styles";
import type { Job } from "../types";
import { formatDate } from "../utils/format";
import { jobStatusPillStyle } from "../utils/statusStyles";

type Props = {
  busy: boolean;
  filterStatus: string;
  isWideLayout: boolean;
  jobs: Job[];
  nextCursor: string | null;
  searchQuery: string;
  selectedJobId: string | null;
  sortOrder: "desc" | "asc";
  onChangeFilterStatus: (value: string) => void;
  onChangeSearchQuery: (value: string) => void;
  onLoadMore: (cursor: string) => void;
  onSelectJob: (jobId: string) => void;
  onToggleSortOrder: () => void;
};

export function JobListPanel({
  busy,
  filterStatus,
  isWideLayout,
  jobs,
  nextCursor,
  searchQuery,
  selectedJobId,
  sortOrder,
  onChangeFilterStatus,
  onChangeSearchQuery,
  onLoadMore,
  onSelectJob,
  onToggleSortOrder,
}: Props) {
  const isEmptyByFilter = jobs.length === 0 && !!searchQuery.trim();

  return (
    <View style={[styles.column, isWideLayout && styles.listColumnDesktop]}>
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>최근 작업</Text>
        <Text style={styles.sectionMeta}>{jobs.length}건</Text>
      </View>
      <View style={styles.panel}>
        <View style={[styles.listControlsShell, isWideLayout && styles.listControlsShellDesktop]}>
          <TextInput
            value={searchQuery}
            onChangeText={onChangeSearchQuery}
            placeholder="파일명 검색"
            style={styles.listSearchInput}
          />
          <View style={styles.listFilterRow}>
            {[
              ["all", "전체"],
              ["completed", "완료"],
              ["failed", "실패"],
              ["processing", "진행중"],
            ].map(([value, label]) => (
              <Pressable
                key={value}
                style={[styles.listFilterChip, filterStatus === value && styles.listFilterChipActive]}
                onPress={() => onChangeFilterStatus(value)}
              >
                <Text style={[styles.listFilterChipLabel, filterStatus === value && styles.listFilterChipLabelActive]}>
                  {label}
                </Text>
              </Pressable>
            ))}
            <Pressable style={styles.listSortButton} onPress={onToggleSortOrder}>
              <Text style={styles.listSortButtonLabel}>{sortOrder === "desc" ? "최신순" : "오래된순"}</Text>
            </Pressable>
          </View>
        </View>
        {isWideLayout ? <View style={styles.listControlsDivider} /> : null}
        <ScrollView
          style={[styles.listScrollArea, isWideLayout && styles.desktopPanelScrollArea]}
          contentContainerStyle={styles.listScrollContent}
          showsVerticalScrollIndicator={isWideLayout}
        >
          {isWideLayout && jobs.length > 0 ? (
            <View style={styles.jobTableHeader}>
              <Text style={[styles.jobTableHeaderText, styles.jobTableHeaderStatus]}>상태</Text>
              <Text style={[styles.jobTableHeaderText, styles.jobTableHeaderFilename]}>파일명</Text>
              <Text style={[styles.jobTableHeaderText, styles.jobTableHeaderTimestamp]}>수정 시각</Text>
            </View>
          ) : null}
          {jobs.length === 0 ? (
            <Text style={styles.emptyState}>
              {isEmptyByFilter ? "검색어나 필터 조건에 맞는 작업이 없습니다." : "아직 업로드한 작업이 없습니다."}
            </Text>
          ) : (
            jobs.map((job) => {
              const selected = job.job_id === selectedJobId;
              return (
                <Pressable
                  key={job.job_id}
                  onPress={() => {
                    startTransition(() => {
                      onSelectJob(job.job_id);
                    });
                  }}
                  style={[
                    isWideLayout ? styles.jobRow : styles.jobCard,
                    selected && (isWideLayout ? styles.jobRowSelected : styles.jobCardSelected),
                  ]}
                >
                  {isWideLayout ? (
                    <>
                      <View style={styles.jobRowStatusCell}>
                        <Text style={jobStatusPillStyle(job.status)}>{STATUS_COPY[job.status]}</Text>
                      </View>
                      <View style={styles.jobRowFilenameCell}>
                        <Text numberOfLines={2} style={styles.jobFilename}>{job.file_name}</Text>
                      </View>
                      <View style={styles.jobRowTimestampCell}>
                        <Text style={styles.jobTimestamp}>{formatDate(job.updated_at || job.created_at)}</Text>
                      </View>
                    </>
                  ) : (
                    <>
                      <View style={styles.jobCardHeader}>
                        <Text style={jobStatusPillStyle(job.status)}>{STATUS_COPY[job.status]}</Text>
                        <Text style={styles.jobTimestamp}>{formatDate(job.updated_at || job.created_at)}</Text>
                      </View>
                      <Text numberOfLines={2} style={styles.jobFilename}>{job.file_name}</Text>
                    </>
                  )}
                </Pressable>
              );
            })
          )}
        </ScrollView>
        {nextCursor ? (
          <Pressable style={styles.loadMoreButton} onPress={() => onLoadMore(nextCursor)}>
            <Text style={styles.loadMoreLabel}>{busy ? "불러오는 중..." : "작업 더 보기"}</Text>
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}

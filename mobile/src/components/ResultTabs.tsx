import React from "react";
import { Pressable, Text, View } from "react-native";

import { styles } from "../styles";

export function ResultTabs({
  tabs,
  value,
  onChange,
}: {
  tabs: Array<{ key: "preview" | "markdown"; label: string }>;
  value: "preview" | "markdown";
  onChange: (next: "preview" | "markdown") => void;
}) {
  return (
    <View style={styles.tabRow}>
      {tabs.map((tab) => {
        const active = tab.key === value;
        return (
          <Pressable
            key={tab.key}
            onPress={() => onChange(tab.key)}
            style={[styles.tabButton, active && styles.tabButtonActive]}
          >
            <Text style={[styles.tabLabel, active && styles.tabLabelActive]}>
              {tab.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

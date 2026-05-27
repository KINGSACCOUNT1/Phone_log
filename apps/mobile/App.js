import { StatusBar } from "expo-status-bar";
import { Audio } from "expo-av";
import * as FileSystem from "expo-file-system";
import { useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import NetInfo from "@react-native-community/netinfo";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:4000";

const CHARACTERS = [
  {
    key: "woman",
    title: "Ava",
    gender: "woman",
    persona: "Warm mentor with natural conversational rhythm",
  },
  {
    key: "man",
    title: "Kai",
    gender: "man",
    persona: "Calm strategist with direct and supportive tone",
  },
];

export default function App() {
  const [character, setCharacter] = useState(CHARACTERS[0]);
  const [recording, setRecording] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [reply, setReply] = useState("Tap and hold to speak.");
  const [error, setError] = useState("");

  const statusText = useMemo(() => {
    if (isRecording) return "Listening...";
    if (isThinking) return "Thinking and speaking...";
    return "Ready";
  }, [isRecording, isThinking]);

  async function startRecording() {
    try {
      setError("");
      const permission = await Audio.requestPermissionsAsync();
      if (!permission.granted) {
        setError("Microphone permission is required.");
        return;
      }

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const rec = new Audio.Recording();
      await rec.prepareToRecordAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
      await rec.startAsync();

      setRecording(rec);
      setIsRecording(true);
    } catch (e) {
      setError(`Failed to start recording: ${e.message}`);
    }
  }

  async function stopRecordingAndSend() {
    const netInfo = await NetInfo.fetch();
    if (!netInfo.isConnected) {
      setError("No internet connection. Please try again later.");
      return;
    }

    if (!recording) return;

    try {
      setIsRecording(false);
      setIsThinking(true);

      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      setRecording(null);

      const formData = new FormData();
      if (uri) {
        formData.append("audio", {
          uri,
          name: "voice-input.m4a",
          type: "audio/m4a",
        });
      }
      formData.append(
        "character",
        JSON.stringify({
          characterName: character.title,
          persona: character.persona,
          gender: character.gender,
        })
      );

      const response = await fetch(`${API_BASE_URL}/api/session/turn`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Request failed");
      }

      setTranscript(data.transcript || "");
      setReply(data.replyText || "No response text returned.");

      if (data.audioBase64) {
        await playBase64Audio(data.audioBase64, data.mimeType || "audio/mpeg");
      }
    } catch (e) {
      setError(`Voice turn failed: ${e.message}`);
    } finally {
      setIsThinking(false);
    }
  }

  async function playBase64Audio(audioBase64, mimeType) {
    const extension = mimeType.includes("mpeg") ? "mp3" : "m4a";
    const fileUri = `${FileSystem.cacheDirectory}reply.${extension}`;

    await FileSystem.writeAsStringAsync(fileUri, audioBase64, {
      encoding: FileSystem.EncodingType.Base64,
    });

    const { sound } = await Audio.Sound.createAsync({ uri: fileUri });
    await sound.playAsync();
  }

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="dark" />
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.eyebrow}>Phone Log Voice</Text>
        <Text style={styles.title}>Character Speech-to-Speech</Text>
        <Text style={styles.subtitle}>
          Synthetic conversational voices only. Do not impersonate real identities.
        </Text>

        <View style={styles.card}>
          <Text style={styles.cardLabel}>Choose a voice</Text>
          <View style={styles.row}>
            {CHARACTERS.map((c) => {
              const isActive = c.key === character.key;
              return (
                <Pressable
                  key={c.key}
                  onPress={() => setCharacter(c)}
                  style={[styles.button, isActive && styles.buttonActive]}
                >
                  <Text
                    style={[styles.buttonText, isActive && styles.buttonTextActive]}
                  >
                    {c.title}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>

        <Text style={styles.status}>{statusText}</Text>
        {isThinking && <ActivityIndicator size="large" color="#0000ff" />}

        <Pressable
          onPressIn={startRecording}
          onPressOut={stopRecordingAndSend}
          style={styles.recordButton}
        >
          <Text style={styles.recordButtonText}>Hold to Talk</Text>
        </Pressable>

        {!!error && (
          <View style={styles.errorCard}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: "#f9f4ec",
  },
  container: {
    padding: 20,
    gap: 16,
  },
  eyebrow: {
    marginTop: 8,
    color: "#9f5e32",
    textTransform: "uppercase",
    letterSpacing: 1,
    fontWeight: "700",
  },
  title: {
    fontSize: 30,
    fontWeight: "800",
    color: "#1f1107",
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 21,
    color: "#4d3726",
  },
  card: {
    borderWidth: 1,
    borderColor: "#e5d4c2",
    borderRadius: 18,
    padding: 14,
    backgroundColor: "#fff9f3",
    gap: 10,
  },
  cardLabel: {
    fontSize: 15,
    fontWeight: "700",
    color: "#3d2518",
  },
  row: {
    flexDirection: "row",
    gap: 8,
  },
  button: {
    borderWidth: 1,
    borderColor: "#d8bca6",
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 999,
    backgroundColor: "#fff",
  },
  buttonActive: {
    backgroundColor: "#7b2f00",
    borderColor: "#7b2f00",
  },
  buttonText: {
    color: "#57351f",
    fontWeight: "700",
  },
  buttonTextActive: {
    color: "#fff8f0",
  },
  persona: {
    color: "#68452f",
    lineHeight: 20,
  },
  micButton: {
    marginTop: 2,
    borderRadius: 20,
    paddingVertical: 18,
    alignItems: "center",
    backgroundColor: "#2a7f62",
  },
  micButtonRecording: {
    backgroundColor: "#c11f1f",
  },
  micButtonText: {
    color: "white",
    fontWeight: "800",
    fontSize: 16,
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  statusText: {
    color: "#57351f",
    fontWeight: "700",
  },
  responseCard: {
    borderRadius: 18,
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#e5d4c2",
    padding: 14,
    gap: 8,
  },
  responseLabel: {
    fontWeight: "800",
    color: "#9f5e32",
    marginTop: 4,
  },
  responseText: {
    color: "#28160c",
    lineHeight: 20,
  },
  errorCard: {
    borderRadius: 12,
    padding: 10,
    backgroundColor: "#ffe9e9",
    borderWidth: 1,
    borderColor: "#e6b4b4",
  },
  errorText: {
    color: "#7a1f1f",
  },
});


import React, { ChangeEvent, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertCircle,
  AudioLines,
  CheckCircle2,
  FileAudio,
  Mic,
  MicOff,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Upload,
  X,
} from 'lucide-react';
import toast from 'react-hot-toast';

import { createVoiceOrder } from '../api/orders';
import { OrderResponse } from '../types/order';
import StatusBadge from '../components/ui/StatusBadge';

const MAX_FILE_BYTES = 10 * 1024 * 1024;
const MAX_DURATION_SECONDS = 30;
const TARGET_SAMPLE_RATE = 16000;

const getErrorMessage = (error: unknown): string => {
  const candidate = error as {
    response?: {
      data?: {
        detail?: string;
      };
    };
    message?: string;
  };

  return (
    candidate.response?.data?.detail ||
    candidate.message ||
    'The audio could not be processed. Please try again.'
  );
};

const formatTime = (seconds: number): string =>
  `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(
    seconds % 60
  ).padStart(2, '0')}`;

/**
 * Converts browser-recorded WebM/Opus audio into
 * standard mono PCM 16-bit WAV at 16 kHz.
 */
const convertToWav = async (file: File): Promise<File> => {
  const AudioContextClass =
    window.AudioContext ||
    (
      window as typeof window & {
        webkitAudioContext?: typeof AudioContext;
      }
    ).webkitAudioContext;

  if (!AudioContextClass) {
    throw new Error('Your browser does not support audio conversion.');
  }

  const audioContext = new AudioContextClass();

  try {
    const arrayBuffer = await file.arrayBuffer();
    const decodedAudio = await audioContext.decodeAudioData(arrayBuffer);

    if (decodedAudio.duration > MAX_DURATION_SECONDS) {
      throw new Error('Audio must be 30 seconds or shorter.');
    }

    const sourceRate = decodedAudio.sampleRate;
    const frameCount = Math.ceil(
      decodedAudio.duration * TARGET_SAMPLE_RATE
    );

    // Mix multiple channels into one mono channel.
    const mono = new Float32Array(decodedAudio.length);

    for (
      let channel = 0;
      channel < decodedAudio.numberOfChannels;
      channel++
    ) {
      const channelData = decodedAudio.getChannelData(channel);

      for (let i = 0; i < channelData.length; i++) {
        mono[i] += channelData[i] / decodedAudio.numberOfChannels;
      }
    }

    // Resample to 16 kHz.
    const resampled = new Float32Array(frameCount);

    for (let i = 0; i < frameCount; i++) {
      const position = (i * sourceRate) / TARGET_SAMPLE_RATE;
      const index = Math.floor(position);
      const fraction = position - index;

      const first = mono[Math.min(index, mono.length - 1)];
      const second = mono[Math.min(index + 1, mono.length - 1)];

      resampled[i] = first + (second - first) * fraction;
    }

    // Create a standard PCM WAV file.
    const dataSize = resampled.length * 2;
    const wavBuffer = new ArrayBuffer(44 + dataSize);
    const view = new DataView(wavBuffer);

    const writeString = (offset: number, value: string) => {
      for (let i = 0; i < value.length; i++) {
        view.setUint8(offset + i, value.charCodeAt(i));
      }
    };

    writeString(0, 'RIFF');
    view.setUint32(4, 36 + dataSize, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, TARGET_SAMPLE_RATE, true);
    view.setUint32(28, TARGET_SAMPLE_RATE * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, dataSize, true);

    for (let i = 0; i < resampled.length; i++) {
      const sample = Math.max(-1, Math.min(1, resampled[i]));

      view.setInt16(
        44 + i * 2,
        sample < 0 ? sample * 32768 : sample * 32767,
        true
      );
    }

    return new File(
      [wavBuffer],
      `${file.name.replace(/\.[^.]+$/, '')}.wav`,
      { type: 'audio/wav' }
    );
  } catch (error) {
    if (error instanceof Error && error.message.includes('30 seconds')) {
      throw error;
    }

    throw new Error(
      'Could not decode this audio file. Please try recording again or upload a supported audio file.'
    );
  } finally {
    await audioContext.close();
  }
};

const VoiceOrders: React.FC = () => {
  const [recording, setRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [order, setOrder] = useState<OrderResponse | null>(null);
  const [error, setError] = useState('');

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const timerRef = useRef<number | null>(null);
  const startedAtRef = useRef(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current !== null) {
        window.clearInterval(timerRef.current);
      }

      streamRef.current?.getTracks().forEach((track) => track.stop());

      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const resetAudio = () => {
    setAudioFile(null);
    setOrder(null);
    setError('');
    setDuration(0);

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setPreviewUrl('');

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const acceptAudio = (file: File) => {
    const validExtension =
      /\.(wav|mp3|ogg|flac|m4a|aac|webm)$/i.test(file.name);

    if (!file.type.startsWith('audio/') && !validExtension) {
      setError(
        'Choose a supported audio file: WAV, MP3, OGG, FLAC, M4A, AAC or WebM.'
      );
      return;
    }

    if (file.size === 0) {
      setError('This audio file is empty. Please choose another file.');
      return;
    }

    if (file.size > MAX_FILE_BYTES) {
      setError('Audio must be 10 MB or smaller.');
      return;
    }

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setAudioFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setOrder(null);
    setError('');
    setDuration(0);
  };

  const startRecording = async () => {
    setError('');

    if (
      !navigator.mediaDevices?.getUserMedia ||
      typeof MediaRecorder === 'undefined'
    ) {
      setError(
        'Audio recording is not supported in this browser. Please upload an audio file instead.'
      );
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });

      streamRef.current = stream;

      const preferredType = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
      ].find((type) => MediaRecorder.isTypeSupported(type));

      const recorder = new MediaRecorder(
        stream,
        preferredType ? { mimeType: preferredType } : undefined
      );

      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onerror = () => {
        setError('Recording failed. Check your microphone and try again.');
        setRecording(false);
      };

      recorder.onstop = () => {
        setRecording(false);

        if (timerRef.current !== null) {
          window.clearInterval(timerRef.current);
          timerRef.current = null;
        }

        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || 'audio/webm',
        });

        const extension = blob.type.includes('ogg')
          ? 'ogg'
          : blob.type.includes('webm')
            ? 'webm'
            : 'wav';

        if (blob.size > 0) {
          const recordedFile = new File(
            [blob],
            `bharatvoice-recording.${extension}`,
            { type: blob.type }
          );

          acceptAudio(recordedFile);
        } else {
          setError('No audio was recorded. Please try again.');
        }

        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        recorderRef.current = null;
      };

      recorderRef.current = recorder;
      startedAtRef.current = Date.now();

      recorder.start(250);

      setRecording(true);
      setDuration(0);

      timerRef.current = window.setInterval(() => {
        const elapsed = Math.floor(
          (Date.now() - startedAtRef.current) / 1000
        );

        setDuration(elapsed);

        if (
          elapsed >= MAX_DURATION_SECONDS &&
          recorder.state === 'recording'
        ) {
          recorder.stop();
        }
      }, 250);
    } catch {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;

      setError(
        'Microphone access was denied or unavailable. Allow microphone permission or upload an audio file.'
      );
    }
  };

  const stopRecording = () => {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }

    if (recorderRef.current?.state === 'recording') {
      recorderRef.current.stop();
    }

    setRecording(false);
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (file) {
      acceptAudio(file);
    }
  };

  const submitAudio = async () => {
    if (!audioFile) return;

    setSubmitting(true);
    setError('');
    setOrder(null);

    try {
      let fileToUpload = audioFile;

      const isWebM =
        audioFile.type.toLowerCase().includes('webm') ||
        audioFile.name.toLowerCase().endsWith('.webm');

      if (isWebM) {
        toast.loading('Converting recording to WAV...', {
          id: 'audio-conversion',
        });

        fileToUpload = await convertToWav(audioFile);

        toast.success('Audio converted successfully.', {
          id: 'audio-conversion',
        });
      }

      if (fileToUpload.size > MAX_FILE_BYTES) {
        throw new Error('Converted audio exceeds the 10 MB upload limit.');
      }

      const result = await createVoiceOrder(fileToUpload);

      setOrder(result);

      toast.success('Voice order processed. Review it before confirming.');
    } catch (err) {
      const message = getErrorMessage(err);

      setError(message);

      toast.error(message, {
        id: 'audio-conversion',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const isClarification = order?.status === 'needs_clarification';

  // Keep display fields flexible while preserving the API response type.
  const displayOrder = order as
    | (OrderResponse & {
        clarification_message?: string | null;
        unsupported_products?: string[];
        items?: Array<{
          product_id?: string;
          product_name?: string;
          name?: string;
          quantity: number;
          unit: string;
          unit_price?: number | null;
        }>;
      })
    | null;

  return (
    <div className="mx-auto max-w-6xl space-y-7">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
            <Sparkles className="h-3.5 w-3.5" />
            AI-powered order capture
          </div>

          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Create a voice order
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
            Speak naturally in Hindi, Hinglish or English. BharatVoice turns
            the recording into a structured order for your review.
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600 shadow-sm">
          <ShieldCheck className="h-4 w-4 text-emerald-600" />
          Shopkeeper approval required
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-900">
                Step 1 · Capture audio
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Record a customer request or upload an existing clip.
              </p>
            </div>

            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
              Max 30 seconds
            </span>
          </div>

          <div className="my-8 flex flex-col items-center rounded-2xl bg-gradient-to-b from-blue-50 to-slate-50 px-5 py-9 text-center">
            <div
              className={`mb-5 flex h-24 w-24 items-center justify-center rounded-full ${
                recording
                  ? 'bg-red-100 ring-8 ring-red-50'
                  : 'bg-blue-100 ring-8 ring-blue-50'
              }`}
            >
              {recording ? (
                <AudioLines className="h-10 w-10 text-red-600" />
              ) : (
                <Mic className="h-10 w-10 text-blue-700" />
              )}
            </div>

            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {formatTime(duration)}
            </p>

            <p className="mt-1 text-sm text-slate-500">
              {recording
                ? 'Recording in progress...'
                : audioFile
                  ? 'Audio ready to process'
                  : 'Ready when you are'}
            </p>

            <div className="mt-6 flex flex-wrap justify-center gap-3">
              {!recording ? (
                <button
                  onClick={startRecording}
                  disabled={submitting}
                  className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Mic className="h-4 w-4" />
                  Start recording
                </button>
              ) : (
                <button
                  onClick={stopRecording}
                  className="inline-flex items-center gap-2 rounded-xl bg-red-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-red-700"
                >
                  <MicOff className="h-4 w-4" />
                  Stop recording
                </button>
              )}

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={recording || submitting}
                className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
              >
                <Upload className="h-4 w-4" />
                Upload audio
              </button>

              <input
                ref={fileInputRef}
                type="file"
                accept="audio/*,.wav,.mp3,.ogg,.flac,.m4a,.aac,.webm"
                className="hidden"
                onChange={handleFileChange}
              />
            </div>

            <p className="mt-4 text-xs text-slate-400">
              Supported: WAV, MP3, OGG, FLAC, M4A, AAC, WebM · Up to 10 MB
            </p>
          </div>

          {audioFile && (
            <div className="rounded-xl border border-blue-100 bg-blue-50/60 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="rounded-lg bg-white p-2 text-blue-700">
                    <FileAudio className="h-5 w-5" />
                  </div>

                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-800">
                      {audioFile.name}
                    </p>

                    <p className="text-xs text-slate-500">
                      {(audioFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>

                <button
                  onClick={resetAudio}
                  disabled={submitting}
                  aria-label="Remove selected audio"
                  className="rounded-lg p-2 text-slate-500 hover:bg-white hover:text-red-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {previewUrl && (
                <audio
                  controls
                  src={previewUrl}
                  className="mt-4 w-full"
                />
              )}

              <button
                onClick={submitAudio}
                disabled={submitting}
                className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-wait disabled:opacity-60"
              >
                {submitting ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Processing voice order...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Transcribe & extract order
                  </>
                )}
              </button>
            </div>
          )}

          {error && (
            <div
              role="alert"
              className="mt-5 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"
            >
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </section>

        <aside className="space-y-5">
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-900">
              How voice ordering works
            </h2>

            <ol className="mt-5 space-y-5">
              {[
                [
                  '01',
                  'Capture the request',
                  'Record the customer speaking naturally.',
                ],
                [
                  '02',
                  'AI transcribes & parses',
                  'Speech becomes text and catalogue items.',
                ],
                [
                  '03',
                  'Review the draft',
                  'Check every product, quantity and unit.',
                ],
                [
                  '04',
                  'Approve the order',
                  'Only you can confirm and save the final order.',
                ],
              ].map(([number, title, description]) => (
                <li key={number} className="flex gap-3">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-xs font-bold text-blue-700">
                    {number}
                  </span>

                  <div>
                    <p className="text-sm font-semibold text-slate-800">
                      {title}
                    </p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                      {description}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          </section>

          <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
            <div className="flex gap-2 text-amber-800">
              <ShieldCheck className="h-5 w-5 shrink-0" />
              <p className="text-sm font-semibold">
                Human approval is always in control
              </p>
            </div>

            <p className="mt-2 text-xs leading-5 text-amber-800/80">
              Transcription does not confirm an order. Review the generated
              items and approve them from the order details screen.
            </p>
          </section>
        </aside>
      </div>

      {order && displayOrder && (
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex flex-col gap-3 border-b border-slate-100 bg-slate-50/70 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-emerald-100 p-2.5 text-emerald-700">
                <CheckCircle2 className="h-5 w-5" />
              </div>

              <div>
                <h2 className="font-semibold text-slate-900">
                  Voice processing complete
                </h2>

                <p className="text-xs text-slate-500">
                  Draft order #{displayOrder.id}
                  {displayOrder.created_at &&
                    ` · Created ${new Date(
                      displayOrder.created_at
                    ).toLocaleString()}`}
                </p>
              </div>
            </div>

            <StatusBadge status={order.status} />
          </div>

          <div className="grid gap-6 p-5 md:grid-cols-[1fr_0.9fr] md:p-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Recognized transcript
              </p>

              <blockquote className="mt-3 rounded-xl border-l-4 border-blue-500 bg-blue-50 p-4 text-sm leading-7 text-slate-800">
                "{displayOrder.transcript || 'No transcript returned'}"
              </blockquote>

              {isClarification && (
                <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
                  <p className="text-sm font-semibold text-amber-800">
                    Clarification required
                  </p>

                  <p className="mt-1 text-sm leading-6 text-amber-800">
                    {displayOrder.clarification_message ||
                      'Please review the order and clarify the missing information.'}
                  </p>
                </div>
              )}

              {displayOrder.unsupported_products &&
                displayOrder.unsupported_products.length > 0 && (
                  <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4">
                    <p className="text-sm font-semibold text-red-800">
                      Unsupported products
                    </p>

                    <div className="mt-2 flex flex-wrap gap-2">
                      {displayOrder.unsupported_products.map(
                        (product, index) => (
                          <span
                            key={`${product}-${index}`}
                            className="rounded-full bg-white px-3 py-1 text-xs font-medium text-red-700"
                          >
                            {product}
                          </span>
                        )
                      )}
                    </div>
                  </div>
                )}
            </div>

            <div>
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-900">
                  Extracted order items
                </h3>

                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                  {displayOrder.items?.length || 0} items
                </span>
              </div>

              {displayOrder.items && displayOrder.items.length > 0 ? (
                <div className="mt-3 space-y-3">
                  {displayOrder.items.map((item, index) => (
                    <div
                      key={`${item.product_id || item.name || index}-${index}`}
                      className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 p-4"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-slate-800">
                          {item.product_name || item.name || 'Product'}
                        </p>

                        <p className="mt-1 text-xs text-slate-500">
                          {item.quantity} {item.unit}
                        </p>
                      </div>

                      {item.unit_price != null && (
                        <p className="shrink-0 text-sm font-semibold text-slate-800">
                          ₹{Number(item.unit_price).toFixed(2)}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-3 rounded-xl border border-dashed border-slate-300 p-5 text-center">
                  <p className="text-sm text-slate-500">
                    No products were extracted.
                  </p>
                </div>
              )}

              <div className="mt-5 rounded-xl bg-slate-50 p-4">
                <p className="text-xs leading-5 text-slate-600">
                  Review the extracted products and quantities before
                  proceeding. No order has been automatically confirmed.
                </p>
              </div>

              <Link
                to={`/orders/${displayOrder.id}`}
                className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
              >
                Review order details
              </Link>
            </div>
          </div>
        </section>
      )}
    </div>
  );
};

export default VoiceOrders;

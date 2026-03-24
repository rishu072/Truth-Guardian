export { };

declare global {
  interface Window {
    gtag: (...args: any[]) => void;
    SpeechRecognition?: typeof SpeechRecognition;
    webkitSpeechRecognition?: typeof SpeechRecognition;
  }

  interface SpeechRecognitionErrorEvent extends Event {
    error: string;
  }

  interface SpeechRecognitionEvent extends Event {
    results: SpeechRecognitionResultList;
  }

  interface SpeechRecognitionResultList {
    [index: number]: SpeechRecognitionResult;
    length: number;
  }

  interface SpeechRecognitionResult {
    [index: number]: SpeechRecognitionAlternative;
    isFinal: boolean;
    length: number;
  }

  interface SpeechRecognitionAlternative {
    transcript: string;
    confidence: number;
  }

  class SpeechRecognition extends EventTarget {
    continuous: boolean;
    interimResults: boolean;
    lang: string;
    start(): void;
    abort(): void;
    onstart: ((this: SpeechRecognition, ev: Event) => any) | null;
    onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
    onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null;
    onend: ((this: SpeechRecognition, ev: Event) => any) | null;
  }
}

import { useState, useRef, useCallback } from 'react'

interface UseSpeechRecognitionReturn {
    isListening: boolean
    transcript: string
    startListening: () => void
    stopListening: () => void
    toggleListening: () => void
    isSupported: boolean
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const getSpeechRecognition = (): any | null => {
    if (typeof window === 'undefined') return null
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const w = window as any
    return w.SpeechRecognition || w.webkitSpeechRecognition || null
}

export function useSpeechRecognition(
    onResult?: (text: string) => void,
    lang: string = 'en-IN',
): UseSpeechRecognitionReturn {
    const [isListening, setIsListening] = useState(false)
    const [transcript, setTranscript] = useState('')
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const recognitionRef = useRef<any>(null)

    const SpeechRecognitionAPI = getSpeechRecognition()
    const isSupported = !!SpeechRecognitionAPI

    const startListening = useCallback(() => {
        if (!SpeechRecognitionAPI) return

        const recognition = new SpeechRecognitionAPI()
        recognition.lang = lang
        recognition.interimResults = true
        recognition.continuous = false
        recognition.maxAlternatives = 1

        recognition.onstart = () => setIsListening(true)

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        recognition.onresult = (event: any) => {
            let final = ''
            let interim = ''
            for (let i = 0; i < event.results.length; i++) {
                const result = event.results[i]
                if (result.isFinal) {
                    final += result[0].transcript
                } else {
                    interim += result[0].transcript
                }
            }
            const text = final || interim
            setTranscript(text)
            if (final && onResult) {
                onResult(final)
            }
        }

        recognition.onerror = () => {
            setIsListening(false)
        }

        recognition.onend = () => {
            setIsListening(false)
        }

        recognitionRef.current = recognition
        recognition.start()
    }, [SpeechRecognitionAPI, lang, onResult])

    const stopListening = useCallback(() => {
        recognitionRef.current?.stop()
        setIsListening(false)
    }, [])

    const toggleListening = useCallback(() => {
        if (isListening) {
            stopListening()
        } else {
            startListening()
        }
    }, [isListening, startListening, stopListening])

    return { isListening, transcript, startListening, stopListening, toggleListening, isSupported }
}

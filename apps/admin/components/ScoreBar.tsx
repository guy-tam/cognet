// רכיב סרגל ציון עם צבע דינמי לפי ערך
interface ScoreBarProps {
  score: number       // ערך בין 0 ל-1
  label: string       // תווית הסרגל
  color?: string      // צבע ידני (אופציונלי, דורס את הברירת המחדל)
}

// פונקציה לקביעת צבע לפי ערך
function getColorClass(score: number, customColor?: string): string {
  if (customColor) return customColor

  if (score >= 0.8) return 'bg-green-500'
  if (score >= 0.6) return 'bg-yellow-400'
  if (score >= 0.4) return 'bg-orange-400'
  return 'bg-red-500'
}

// פונקציה לקביעת צבע טקסט לפי ערך
function getTextColorClass(score: number): string {
  if (score >= 0.8) return 'text-green-700'
  if (score >= 0.6) return 'text-yellow-700'
  if (score >= 0.4) return 'text-orange-700'
  return 'text-red-700'
}

export default function ScoreBar({ score, label, color }: ScoreBarProps) {
  const pct = Math.round(score * 100)
  const barColor = getColorClass(score, color)
  const textColor = getTextColorClass(score)

  return (
    <div className="w-full">
      {/* שורת תווית וערך */}
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-gray-600">{label}</span>
        <span className={`text-sm font-semibold ${textColor}`}>{pct}%</span>
      </div>

      {/* רקע הסרגל */}
      <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
        {/* מילוי הסרגל */}
        <div
          className={`h-2 rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={label}
        />
      </div>
    </div>
  )
}

// רכיב סרגל ציון פרמיום עם גרדיאנט דינמי
interface ScoreBarProps {
  score: number       // ערך בין 0 ל-1
  label: string       // תווית הסרגל
  color?: string      // צבע ידני (אופציונלי, דורס את הברירת המחדל)
  compact?: boolean   // מצב קומפקטי — גובה מצומצם
}

// פונקציה לקביעת גרדיאנט לפי סף ציון
function getGradientClass(score: number, customColor?: string): string {
  if (customColor) return customColor

  const pct = score * 100
  if (pct >= 70) return 'bg-gradient-to-r from-emerald-400 to-green-500'
  if (pct >= 50) return 'bg-gradient-to-r from-blue-400 to-indigo-500'
  if (pct >= 30) return 'bg-gradient-to-r from-amber-400 to-yellow-500'
  return 'bg-gradient-to-r from-slate-300 to-slate-400'
}

// פונקציה לקביעת צבע טקסט לפי ערך
function getTextColorClass(score: number): string {
  const pct = score * 100
  if (pct >= 70) return 'text-emerald-600'
  if (pct >= 50) return 'text-indigo-600'
  if (pct >= 30) return 'text-amber-600'
  return 'text-slate-500'
}

export default function ScoreBar({ score, label, color, compact = false }: ScoreBarProps) {
  const pct = Math.round(score * 100)
  const gradientClass = getGradientClass(score, color)
  const textColor = getTextColorClass(score)
  const barHeight = compact ? 'h-2' : 'h-3'

  return (
    <div className="w-full">
      {/* שורת תווית וערך */}
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-sm text-slate-600 font-medium">{label}</span>
        <span className={`text-sm font-semibold tabular-nums ${textColor}`}>
          {pct}%
        </span>
      </div>

      {/* רקע הסרגל — צורת גלולה */}
      <div className={`w-full bg-slate-100 rounded-full ${barHeight} overflow-hidden`}>
        {/* מילוי הסרגל עם גרדיאנט ואנימציית מעבר */}
        <div
          className={[
            'rounded-full transition-all duration-700 ease-out',
            barHeight,
            gradientClass,
          ].join(' ')}
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

interface ArticleStampProps {
  articleNumber: number;
  title: string;
}

export function ArticleStamp({ articleNumber, title }: ArticleStampProps) {
  return (
    <div className="flex items-center gap-3 group">
      <div
        className="shrink-0 w-11 h-11 rounded-full border-[1.5px] flex items-center justify-center
                   font-mono text-[13px] font-semibold tracking-tight
                   transition-colors"
        style={{
          borderColor: "var(--brass)",
          color: "var(--brass-bright)",
        }}
      >
        {articleNumber}
      </div>
      <div className="flex flex-col">
        <span
          className="font-mono text-[10px] uppercase tracking-[0.14em]"
          style={{ color: "var(--brass)" }}
        >
          Article {articleNumber}
        </span>
        <span className="text-sm" style={{ color: "var(--slate)" }}>
          {title}
        </span>
      </div>
    </div>
  );
}

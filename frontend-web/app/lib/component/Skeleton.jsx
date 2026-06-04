/**
 * 파일명: Skeleton.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Skeleton UI 컴포넌트 구현
 */

const Skeleton = ({ className = '', variant = 'rect', lines = 1, circleSize = 40, ...props }) => {

  const baseClassName = 'bg-gray-200/70 animate-pulse';
  const skeletonLineList = [];
  for (let lineIndex = 0; lineIndex < Math.max(1, lines); lineIndex += 1) {
    skeletonLineList.push(lineIndex);
  }

  if (variant === 'text') {
    return (
      <div className={`space-y-2 ${className}`.trim()} {...props}>
        {skeletonLineList.map((lineIndex) => (
          <div key={lineIndex} className={`${baseClassName} h-3 w-full rounded`}></div>
        ))}
      </div>
    );
  }
  if (variant === 'circle') {
    const circleSizeClassMap = {
      16: 'w-4 h-4',
      20: 'w-5 h-5',
      24: 'w-6 h-6',
      32: 'w-8 h-8',
      40: 'w-10 h-10',
      48: 'w-12 h-12',
      56: 'w-14 h-14',
      64: 'w-16 h-16',
    };
    const normalizedSize = Number(circleSize);
    const circleSizeClassName = Number.isFinite(normalizedSize) && circleSizeClassMap[normalizedSize]
      ? circleSizeClassMap[normalizedSize]
      : circleSizeClassMap[40];
    return <div className={`${baseClassName} rounded-full ${circleSizeClassName}`} {...props}></div>;
  }
  return <div className={`${baseClassName} rounded ${className}`} {...props}></div>;
};

export default Skeleton;

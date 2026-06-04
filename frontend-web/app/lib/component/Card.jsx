/**
 * 파일명: Card.jsx
 * 작성자: LSH
 * 갱신일: 2025-09-13
 * 설명: Card UI 컴포넌트 구현
 */
const Card = ({
  title,
  subtitle,
  actions,
  children,
  footer,
  className = '',
  headerClassName = '',
  bodyClassName = '',
  footerClassName = '',
  id,
  ...props
}) => {

  const headingId = id ? `${id}-title` : undefined;
  return (
    <div
      className={`rounded-lg border border-gray-200 bg-white shadow-sm ${className}`.trim()}
      aria-labelledby={headingId}
      {...props}
    >
      {(title || actions || subtitle) && (
        <div className={`flex flex-col gap-3 border-b border-gray-200 p-4 sm:flex-row sm:items-start sm:justify-between ${headerClassName}`.trim()}>
          <div>
            {title && (
              <h3 id={headingId} className="text-base font-semibold text-gray-900">{title}</h3>
            )}
            {subtitle && (
              <p className="mt-0.5 text-sm text-gray-500">{subtitle}</p>
            )}
          </div>
          {actions && (
            <div className="w-full sm:w-auto sm:shrink-0">{actions}</div>
          )}
        </div>
      )}
      <div className={`p-4 min-w-0 w-full ${bodyClassName}`.trim()}>
        {children}
      </div>
      {footer && (
        <div className={`border-t border-gray-200 p-3 text-sm text-gray-600 ${footerClassName}`.trim()}>
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;

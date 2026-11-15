type ApiUnavailableStateProps = {
  message: string;
};

export default function ApiUnavailableState({ message }: ApiUnavailableStateProps) {
  const isApiUnavailable = message.includes("127.0.0.1:8000");

  if (!isApiUnavailable) {
    return <div className="empty-state">{message}</div>;
  }

  return (
    <div className="empty-state empty-state--detailed">
      <strong>Backend недоступен</strong>
      <p>{message}</p>
      <code>.\start-dev.ps1</code>
    </div>
  );
}

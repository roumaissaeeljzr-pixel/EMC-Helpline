import "./PagePlaceholder.css";

function PagePlaceholder({ title, description, phase }) {
  return (
    <div className="placeholder-page">
      <h2>{title}</h2>
      {description && (
        <p className="placeholder-description">{description}</p>
      )}
      <div className="placeholder-badge">{phase}</div>
    </div>
  );
}

export default PagePlaceholder;
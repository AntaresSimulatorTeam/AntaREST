import i18n from "../../../i18n";

export function createSaveButton(onClick: VoidFunction) {
  const saveBtn = document.createElement("button");
  saveBtn.classList.add("jsoneditor-separator");
  saveBtn.title = i18n.t("global.save");
  saveBtn.style.backgroundImage =
    "url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAA7E" +
    "AAAOxAGVKw4bAAAA6klEQVQ4jaXSMUoDYRQE4G+XJYhFkNR2ggewtvQE3kS09QQKIjmDWHsEwcIrWGulIiIhBh" +
    "HHIptkDYlhdcr3v5l5/3tTJNlHHxu4wYPlqLCHM5wWRUGS+8ywuYiV5DzJdZJukqu69ySJCt1G79cS5x3sooPP" +
    "unaEp7Iea5XAMhyXLQnzqCo0RdaXNF7iFkOsNR+KJO+N4iOef3Essd0wHc0LtMVossAXbNUjsniZza92cIfeRG" +
    "BQFMVrC+ePJAP0JqptzzfllH8kT/HfHCjNovlngTc/49yGO6xwiH6SC+MzrtpJaZybHg6+AW/yWkXws02vAAAA" +
    "AElFTkSuQmCC)";
  saveBtn.style.backgroundRepeat = "no-repeat";
  saveBtn.style.backgroundPosition = "center";

  saveBtn.addEventListener("click", onClick);

  return saveBtn;
}

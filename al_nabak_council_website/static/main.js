function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem('theme', theme);
  } catch (error) {
    // Storage can be unavailable in restricted browser contexts.
  }
}

document.addEventListener('DOMContentLoaded', function () {
  var toggle = document.getElementById('theme-toggle');
  var alertButtons = document.querySelectorAll('.alert-close');
  var watchedForms = document.querySelectorAll('form[data-watch-changes]');
  var allForms = document.querySelectorAll('form');
  var searchInput = document.getElementById('project-search');
  var groupAttributionPanel = document.querySelector('[data-group-attribution]');
  var attributionInputs = document.querySelectorAll('input[name="attribution_type"]');
  var customSites = document.querySelector('[data-custom-sites]');
  var customSiteTemplate = document.getElementById('custom-site-template');
  var addCustomSiteButton = document.querySelector('[data-add-custom-site]');
  var roleSelect = document.querySelector('select[name="role"]');
  var roleCards = document.querySelectorAll('[data-role-card]');
  var adminPermissionNote = document.querySelector('[data-admin-permission-note]');
  var permissionDefaultToggle = document.querySelector('[data-permission-default-toggle]');
  var permissionOverrides = document.querySelector('[data-permission-overrides]');
  var suggestionTarget = document.querySelector('select[name="target_type"]');
  var suggestionProjectPanel = document.querySelector('[data-suggestion-project]');
  var textSizeDecrease = document.querySelector('[data-text-size-decrease]');
  var textSizeReset = document.querySelector('[data-text-size-reset]');
  var textSizeIncrease = document.querySelector('[data-text-size-increase]');
  var textSizeStatus = document.querySelector('[data-text-size-status]');
  var textSizeControls = document.querySelector('.text-size-controls');
  var richEditors = document.querySelectorAll('[data-rich-editor]');
  var textSizeMin = -2;
  var textSizeMax = 3;

  function markFormDirty(element) {
    var form = element ? element.closest('form[data-watch-changes]') : null;
    if (form) {
      form.dataset.dirty = 'true';
    }
  }

  alertButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      var alert = button.closest('.alert');
      if (alert) {
        alert.remove();
      }
    });
  });

  allForms.forEach(function (form) {
    var confirmed = false;
    form.addEventListener('submit', function (event) {
      var submitter = event.submitter || form.querySelector('button[type="submit"], input[type="submit"]');
      var message = submitter ? submitter.getAttribute('data-confirm') : null;

      if (message && !confirmed) {
        if (!window.confirm(message)) {
          event.preventDefault();
          return;
        }
        confirmed = true;
      }

      if (submitter && submitter.tagName === 'BUTTON') {
        submitter.classList.add('is-loading');
        submitter.setAttribute('aria-busy', 'true');
      }
      form.dataset.submitted = 'true';
    });
  });

  watchedForms.forEach(function (form) {
    form.dataset.dirty = 'false';
    form.addEventListener('input', function () {
      form.dataset.dirty = 'true';
    });
    form.addEventListener('change', function () {
      form.dataset.dirty = 'true';
    });
  });

  window.addEventListener('beforeunload', function (event) {
    var dirtyForm = Array.prototype.find.call(watchedForms, function (form) {
      return form.dataset.dirty === 'true' && form.dataset.submitted !== 'true';
    });
    if (dirtyForm) {
      event.preventDefault();
      event.returnValue = '';
    }
  });

  document.addEventListener('keydown', function (event) {
    var tagName = document.activeElement ? document.activeElement.tagName : '';
    var isTyping = tagName === 'INPUT' || tagName === 'TEXTAREA' || tagName === 'SELECT';
    if (event.key === '/' && searchInput && !isTyping && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault();
      searchInput.focus();
    }
  });

  function syncDonationGroupFields() {
    if (!groupAttributionPanel || !attributionInputs.length) return;

    var groupSelected = Array.prototype.some.call(attributionInputs, function (input) {
      return input.checked && input.value === 'group';
    });

    groupAttributionPanel.hidden = !groupSelected;
    groupAttributionPanel.querySelectorAll('select, input, textarea').forEach(function (field) {
      field.disabled = !groupSelected;
    });
  }

  attributionInputs.forEach(function (input) {
    input.addEventListener('change', syncDonationGroupFields);
  });
  syncDonationGroupFields();

  function wireCustomSiteRow(row) {
    var removeButton = row.querySelector('[data-remove-custom-site]');
    if (!removeButton) return;
    removeButton.addEventListener('click', function () {
      row.remove();
      markFormDirty(removeButton);
    });
  }

  if (customSites) {
    customSites.querySelectorAll('[data-custom-site-row]').forEach(wireCustomSiteRow);
  }

  if (addCustomSiteButton && customSites && customSiteTemplate) {
    addCustomSiteButton.addEventListener('click', function () {
      var index = Date.now().toString();
      var html = customSiteTemplate.innerHTML.replace(/__index__/g, index);
      customSites.insertAdjacentHTML('beforeend', html);
      var row = customSites.querySelector('[data-custom-site-row]:last-child');
      if (row) {
        wireCustomSiteRow(row);
        var firstInput = row.querySelector('input.control');
        if (firstInput) {
          firstInput.focus();
        }
      }
      markFormDirty(addCustomSiteButton);
    });
  }

  function syncRolePermissionHints() {
    if (!roleSelect) return;
    var selectedRole = roleSelect.value;

    roleCards.forEach(function (card) {
      var isActive = card.getAttribute('data-role-card') === selectedRole;
      card.classList.toggle('active', isActive);
      card.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });

    if (adminPermissionNote) {
      adminPermissionNote.hidden = selectedRole !== 'admin';
    }

    if (permissionOverrides) {
      permissionOverrides.querySelectorAll('[data-permission-row]').forEach(function (row) {
        var defaultValue = row.getAttribute('data-default-' + selectedRole);
        var label = row.querySelector('[data-permission-default-text]');
        if (!label || defaultValue === null) return;
        label.textContent = defaultValue === '1' ? label.dataset.allowedLabel : label.dataset.blockedLabel;
      });
    }
  }

  if (roleSelect) {
    roleSelect.addEventListener('change', syncRolePermissionHints);
    roleCards.forEach(function (card) {
      card.setAttribute('role', 'button');
      card.setAttribute('tabindex', '0');
      card.addEventListener('click', function () {
        roleSelect.value = card.getAttribute('data-role-card');
        roleSelect.dispatchEvent(new Event('change', { bubbles: true }));
        markFormDirty(roleSelect);
      });
      card.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          card.click();
        }
      });
    });
    syncRolePermissionHints();
  }

  function syncSuggestionProjectField() {
    if (!suggestionTarget || !suggestionProjectPanel) return;
    var isProjectSuggestion = suggestionTarget.value === 'project_tracker';
    suggestionProjectPanel.hidden = !isProjectSuggestion;
    suggestionProjectPanel.querySelectorAll('select, input, textarea').forEach(function (field) {
      field.disabled = !isProjectSuggestion;
    });
  }

  if (suggestionTarget && suggestionProjectPanel) {
    suggestionTarget.addEventListener('change', syncSuggestionProjectField);
    syncSuggestionProjectField();
  }

  function syncPermissionOverrides() {
    if (!permissionDefaultToggle || !permissionOverrides) return;
    var isDefaultMode = permissionDefaultToggle.checked;
    permissionOverrides.classList.toggle('is-default-mode', isDefaultMode);
    permissionOverrides.querySelectorAll('[data-permission-row]').forEach(function (row) {
      var radios = row.querySelectorAll('input[type="radio"]');
      var checked = row.querySelector('input[type="radio"]:checked');
      if (isDefaultMode) {
        if (checked && checked.value !== 'default') {
          row.dataset.customPermissionState = checked.value;
        }
        var defaultRadio = row.querySelector('input[type="radio"][value="default"]');
        if (defaultRadio) {
          defaultRadio.checked = true;
        }
      } else if (row.dataset.customPermissionState) {
        var customRadio = row.querySelector('input[type="radio"][value="' + row.dataset.customPermissionState + '"]');
        if (customRadio) {
          customRadio.checked = true;
        }
      }
      radios.forEach(function (input) {
        input.disabled = isDefaultMode;
      });
    });
  }

  if (permissionDefaultToggle && permissionOverrides) {
    permissionDefaultToggle.addEventListener('change', syncPermissionOverrides);
    syncPermissionOverrides();
  }

  function getTextSizeLevel() {
    var current = parseInt(document.documentElement.dataset.textSize || '0', 10);
    return Number.isNaN(current) ? 0 : Math.max(textSizeMin, Math.min(textSizeMax, current));
  }

  function setTextSizeLevel(level) {
    var nextLevel = Math.max(textSizeMin, Math.min(textSizeMax, level));
    document.documentElement.dataset.textSize = String(nextLevel);
    try {
      localStorage.setItem('textSizeLevel', String(nextLevel));
    } catch (error) {
      // Storage can be unavailable in restricted browser contexts.
    }
    if (textSizeDecrease) {
      textSizeDecrease.disabled = nextLevel <= textSizeMin;
    }
    if (textSizeIncrease) {
      textSizeIncrease.disabled = nextLevel >= textSizeMax;
    }
    if (textSizeReset) {
      textSizeReset.disabled = nextLevel === 0;
    }
    if (textSizeStatus) {
      var prefix = textSizeControls ? textSizeControls.getAttribute('data-text-size-status-prefix') : 'Text size level';
      var readableLevel = nextLevel > 0 ? '+' + nextLevel : String(nextLevel);
      textSizeStatus.textContent = prefix + ': ' + readableLevel;
    }
  }

  if (textSizeDecrease && textSizeReset && textSizeIncrease) {
    textSizeDecrease.addEventListener('click', function () {
      setTextSizeLevel(getTextSizeLevel() - 1);
    });
    textSizeReset.addEventListener('click', function () {
      setTextSizeLevel(0);
    });
    textSizeIncrease.addEventListener('click', function () {
      setTextSizeLevel(getTextSizeLevel() + 1);
    });
    setTextSizeLevel(getTextSizeLevel());
  }

  function initRichEditor(editor) {
    var targetId = editor.getAttribute('data-target');
    var source = targetId ? document.getElementById(targetId) : null;
    var surface = editor.querySelector('[data-rich-surface]');
    if (!source || !surface) return;

    function syncSource(markDirty) {
      source.value = surface.innerHTML.trim();
      if (markDirty) {
        markFormDirty(surface);
      }
    }

    function runCommand(command, value) {
      surface.focus();
      if (command === 'formatBlock') {
        document.execCommand(command, false, value || 'p');
      } else {
        document.execCommand(command, false, value || null);
      }
      syncSource(true);
    }

    surface.addEventListener('input', function () {
      syncSource(true);
    });
    surface.addEventListener('blur', function () {
      syncSource(true);
    });

    editor.querySelectorAll('[data-rich-command]').forEach(function (control) {
      control.addEventListener('click', function () {
        if (control.tagName === 'SELECT') return;
        runCommand(control.getAttribute('data-rich-command'), control.getAttribute('data-rich-value'));
      });
      control.addEventListener('change', function () {
        runCommand(control.getAttribute('data-rich-command'), control.value);
      });
    });

    var form = editor.closest('form');
    if (form) {
      form.addEventListener('submit', function () {
        syncSource(false);
      });
    }
    syncSource(false);
  }

  richEditors.forEach(initRichEditor);

  if (!toggle) return;

  var icon = toggle.querySelector('i');
  function syncIcon() {
    var isDark = document.documentElement.dataset.theme === 'dark';
    if (icon) {
      icon.className = isDark ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
    }
    toggle.setAttribute('aria-pressed', isDark ? 'true' : 'false');
    toggle.setAttribute('aria-label', isDark ? toggle.dataset.lightLabel : toggle.dataset.darkLabel);
  }

  syncIcon();
  toggle.addEventListener('click', function () {
    var nextTheme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    syncIcon();
  });
});

(function(global) {
  'use strict';

  // Shared schedule metadata for the public-facing countdown.
  const DAILY_WATCH_TIME_ZONE = 'America/New_York';
  const DAILY_WATCH_SCHEDULE = { hour: 20, minute: 5, activeWeekdays: [0, 1, 2, 3, 4] };
  const DAILY_WATCH_WEEKDAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const DAILY_WATCH_WEEKDAY_INDEX = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };

  // Cache Intl formatters because the countdown updates every second in the browser.
  const PARTS_FORMATTER_CACHE = new Map();
  const WEEKDAY_FORMATTER_CACHE = new Map();

  function getPartsFormatter(timeZone) {
    if (!PARTS_FORMATTER_CACHE.has(timeZone)) {
      PARTS_FORMATTER_CACHE.set(timeZone, new Intl.DateTimeFormat('en-US', {
        timeZone: timeZone,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hourCycle: 'h23'
      }));
    }
    return PARTS_FORMATTER_CACHE.get(timeZone);
  }

  function getWeekdayFormatter(timeZone) {
    if (!WEEKDAY_FORMATTER_CACHE.has(timeZone)) {
      WEEKDAY_FORMATTER_CACHE.set(timeZone, new Intl.DateTimeFormat('en-US', {
        timeZone: timeZone,
        weekday: 'short'
      }));
    }
    return WEEKDAY_FORMATTER_CACHE.get(timeZone);
  }

  function getDailyWatchParts(date, timeZone = DAILY_WATCH_TIME_ZONE) {
    const values = {};
    getPartsFormatter(timeZone).formatToParts(date).forEach(function(part) {
      if (part.type !== 'literal') values[part.type] = part.value;
    });
    return {
      year: Number(values.year),
      month: Number(values.month),
      day: Number(values.day),
      hour: Number(values.hour),
      minute: Number(values.minute),
      second: Number(values.second)
    };
  }

  function getDailyWatchWeekdayIndex(date, timeZone = DAILY_WATCH_TIME_ZONE) {
    return DAILY_WATCH_WEEKDAY_INDEX[getWeekdayFormatter(timeZone).format(date)];
  }

  function getTimeZoneOffsetMinutes(date, timeZone = DAILY_WATCH_TIME_ZONE) {
    const parts = getDailyWatchParts(date, timeZone);
    const asUtc = Date.UTC(parts.year, parts.month - 1, parts.day, parts.hour, parts.minute, parts.second);
    return Math.round((asUtc - date.getTime()) / 60000);
  }

  function zonedDateTimeToUtcMs(year, month, day, hour, minute, second = 0, timeZone = DAILY_WATCH_TIME_ZONE) {
    const wallClockMs = Date.UTC(year, month - 1, day, hour, minute, second);
    let offsetMinutes = getTimeZoneOffsetMinutes(new Date(wallClockMs), timeZone);
    let utcMs = wallClockMs - offsetMinutes * 60 * 1000;
    const refinedOffsetMinutes = getTimeZoneOffsetMinutes(new Date(utcMs), timeZone);
    if (refinedOffsetMinutes !== offsetMinutes) {
      utcMs = wallClockMs - refinedOffsetMinutes * 60 * 1000;
    }
    return utcMs;
  }

  function computeNextDailyWatchRun(now = new Date(), schedule = DAILY_WATCH_SCHEDULE, timeZone = DAILY_WATCH_TIME_ZONE) {
    const nowMs = now.getTime();
    const todayParts = getDailyWatchParts(now, timeZone);
    const baseNoonUtcMs = zonedDateTimeToUtcMs(todayParts.year, todayParts.month, todayParts.day, 12, 0, 0, timeZone);

    for (let dayOffset = 0; dayOffset < 8; dayOffset += 1) {
      const probeDate = new Date(baseNoonUtcMs + dayOffset * 24 * 60 * 60 * 1000);
      const probeParts = getDailyWatchParts(probeDate, timeZone);
      const probeWeekday = getDailyWatchWeekdayIndex(probeDate, timeZone);
      if (!schedule.activeWeekdays.includes(probeWeekday)) continue;

      const candidateUtcMs = zonedDateTimeToUtcMs(
        probeParts.year,
        probeParts.month,
        probeParts.day,
        schedule.hour,
        schedule.minute,
        0,
        timeZone
      );

      if (candidateUtcMs > nowMs) {
        return {
          date: new Date(candidateUtcMs),
          weekday: probeWeekday
        };
      }
    }

    return null;
  }

  function formatCountdownDuration(ms) {
    const totalSeconds = Math.max(0, Math.floor(ms / 1000));
    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    const parts = [];
    if (days > 0) parts.push(days + 'd');
    parts.push(String(hours).padStart(days > 0 ? 2 : 1, '0') + 'h');
    parts.push(String(minutes).padStart(2, '0') + 'm');
    parts.push(String(seconds).padStart(2, '0') + 's');
    return parts.join(' ');
  }

  function formatDailyWatchRunLabel(run, schedule = DAILY_WATCH_SCHEDULE) {
    return DAILY_WATCH_WEEKDAY_LABELS[run.weekday] + ' '
      + String(schedule.hour).padStart(2, '0')
      + ':'
      + String(schedule.minute).padStart(2, '0')
      + ' ET';
  }

  function updateDailyWatchCountdown(doc = global.document, now = new Date()) {
    if (!doc) return null;

    const valueEl = doc.getElementById('daily-watch-countdown-value');
    const metaEl = doc.getElementById('daily-watch-countdown-meta');
    if (!valueEl || !metaEl) return null;

    const nextRun = computeNextDailyWatchRun(now);
    if (!nextRun) {
      valueEl.textContent = 'Schedule unavailable';
      metaEl.textContent = '20:05 ET Sunday–Thursday · about 5 minutes after arXiv\'s daily announcement.';
      return null;
    }

    const remainingMs = nextRun.date.getTime() - now.getTime();
    valueEl.textContent = 'in ' + formatCountdownDuration(remainingMs);
    metaEl.textContent = '20:05 ET Sunday–Thursday · next fetch '
      + formatDailyWatchRunLabel(nextRun)
      + ' · about 5 minutes after arXiv\'s daily announcement.';
    return nextRun;
  }

  function startDailyWatchCountdown(doc = global.document) {
    if (!doc || typeof global.setInterval !== 'function') return null;
    return global.setInterval(function() {
      updateDailyWatchCountdown(doc, new Date());
    }, 1000);
  }

  const api = {
    DAILY_WATCH_TIME_ZONE,
    DAILY_WATCH_SCHEDULE,
    computeNextDailyWatchRun,
    formatCountdownDuration,
    formatDailyWatchRunLabel,
    getDailyWatchParts,
    getDailyWatchWeekdayIndex,
    getTimeZoneOffsetMinutes,
    startDailyWatchCountdown,
    updateDailyWatchCountdown,
    zonedDateTimeToUtcMs
  };

  global.DAILY_WATCH_COUNTDOWN = api;
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})(typeof window !== 'undefined' ? window : globalThis);

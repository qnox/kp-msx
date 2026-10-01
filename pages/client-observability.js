(function () {
    'use strict';

    var endpoint = '/msx/client-report';
    var session = Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10);
    var lastEvent = {};

    function clean(value) {
        return String(value == null ? '' : value)
            .replace(/https?:\/\/\S+/gi, '[url]')
            .slice(0, 500);
    }

    function mediaState() {
        var player = document.getElementById('player');
        if (!player) {
            return {};
        }
        return {
            ready_state: player.readyState,
            network_state: player.networkState,
            current_time: isFinite(player.currentTime) ? player.currentTime : 0,
            duration: isFinite(player.duration) ? player.duration : 0
        };
    }

    function report(eventName, details, rateLimit) {
        var now = Date.now();
        if (rateLimit && lastEvent[eventName] && now - lastEvent[eventName] < rateLimit) {
            return;
        }
        lastEvent[eventName] = now;

        var payload = mediaState();
        payload.event = eventName;
        payload.session = session;
        if (details) {
            Object.keys(details).forEach(function (key) {
                payload[key] = typeof details[key] === 'string' ? clean(details[key]) : details[key];
            });
        }

        try {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', endpoint, true);
            xhr.timeout = 2000;
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(JSON.stringify(payload));
        } catch (_error) {
            // Telemetry must never interfere with playback.
        }
    }

    function wrapMethod(target, name, eventName, detailArgument) {
        if (!target || typeof target[name] !== 'function') {
            return;
        }
        var original = target[name];
        target[name] = function () {
            var details = {};
            if (detailArgument != null && arguments.length > detailArgument) {
                details.detail = clean(arguments[detailArgument]);
            }
            report(eventName, details);
            return original.apply(this, arguments);
        };
    }

    function installPluginHooks() {
        if (!window.TVXVideoPlugin) {
            report('tvx_plugin_missing');
            return;
        }

        var originalSetup = window.TVXVideoPlugin.setupPlayer;
        if (typeof originalSetup === 'function') {
            window.TVXVideoPlugin.setupPlayer = function (player) {
                wrapMethod(player, 'init', 'plugin_init');
                wrapMethod(player, 'ready', 'plugin_ready');
                wrapMethod(player, 'dispose', 'plugin_dispose');
                wrapMethod(player, 'handleRequest', 'plugin_request', 0);
                wrapMethod(player, 'handleData', 'plugin_data', 0);
                report('plugin_setup');
                return originalSetup.apply(this, arguments);
            };
        }

        wrapMethod(window.TVXVideoPlugin, 'error', 'plugin_error', 0);
        wrapMethod(window.TVXVideoPlugin, 'warn', 'plugin_warning', 0);
        wrapMethod(window.TVXVideoPlugin, 'init', 'tvx_init');
    }

    function installMediaHooks() {
        var player = document.getElementById('player');
        if (!player) {
            report('video_element_missing');
            return;
        }

        ['loadedmetadata', 'canplay', 'playing', 'pause', 'ended'].forEach(function (name) {
            player.addEventListener(name, function () {
                report('media_' + name);
            });
        });

        ['waiting', 'stalled'].forEach(function (name) {
            player.addEventListener(name, function () {
                report('media_' + name, null, 10000);
            });
        });

        player.addEventListener('error', function () {
            var error = player.error;
            report('media_error', {
                code: error ? error.code : 0,
                detail: error && error.message ? error.message : 'Unknown media error'
            });
        });
        player.addEventListener('abort', function () {
            report('media_abort');
        });
    }

    window.addEventListener('error', function (event) {
        report('window_error', {detail: event.message || 'Unknown window error'});
    });
    window.addEventListener('unhandledrejection', function (event) {
        report('promise_rejection', {detail: event.reason || 'Unhandled promise rejection'});
    });
    window.addEventListener('load', function () {
        installMediaHooks();
        report('page_loaded');
    });
    window.addEventListener('beforeunload', function () {
        report('page_unloading');
    });

    installPluginHooks();
    report('telemetry_loaded');
}());

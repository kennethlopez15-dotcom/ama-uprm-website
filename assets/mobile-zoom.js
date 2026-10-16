/* Keep mobile pinch gestures above the initial scale without disabling zoom-in.
   Safari ignores viewport minimum-scale; its gesture events need a separate guard.
   This cannot control Safari's toolbar Page Zoom or OS accessibility settings. */
(function () {
  'use strict';
  if (!('ontouchstart' in window) && !navigator.maxTouchPoints) return;

  var gestureScale = 0, touchScale = 1, touchDistance = 0;
  var active = { passive: false, capture: true };
  var passive = { passive: true, capture: true };

  function currentScale() {
    return window.visualViewport ? window.visualViewport.scale : 1;
  }
  function distance(touches) {
    var x = touches[0].screenX - touches[1].screenX;
    var y = touches[0].screenY - touches[1].screenY;
    return Math.hypot(x, y);
  }
  function rememberTouches(event) {
    touchDistance = event.touches.length === 2 ? distance(event.touches) : 0;
    touchScale = Math.max(1, currentScale());
  }
  function preventBelowInitial(event, scale) {
    if (scale > 0 && scale < 1 && event.cancelable) event.preventDefault();
  }

  document.addEventListener('gesturestart', function () {
    gestureScale = Math.max(1, currentScale());
  }, passive);
  document.addEventListener('gesturechange', function (event) {
    if (gestureScale) preventBelowInitial(event, gestureScale * event.scale);
  }, active);
  document.addEventListener('gestureend', function () { gestureScale = 0; }, passive);

  // Touch fallback also catches an inward pinch before Safari's native zoom begins.
  document.addEventListener('touchstart', rememberTouches, passive);
  document.addEventListener('touchmove', function (event) {
    if (event.touches.length === 2 && touchDistance) {
      preventBelowInitial(event, touchScale * distance(event.touches) / touchDistance);
    }
  }, active);
  document.addEventListener('touchend', rememberTouches, passive);
  document.addEventListener('touchcancel', function () {
    touchDistance = 0;
    gestureScale = 0;
  }, passive);
})();

export const vertex = `
attribute vec2 aPosition;
varying vec2 vUv;
void main() {
  vUv = vec2(aPosition.x * .5 + .5, .5 - aPosition.y * .5);
  gl_Position = vec4(aPosition, 0., 1.);
}`;
export const fragment = `
precision mediump float;
varying vec2 vUv;
uniform sampler2D uPhoto;
uniform sampler2D uDrawing;
uniform sampler2D uControl;
uniform vec2 uScale;
uniform vec2 uOffset;
uniform float uResolve;
uniform float uVelocity;
void main() {
  vec2 uv = vUv * uScale + uOffset;
  vec3 photo = texture2D(uPhoto, uv).rgb;
  if (uResolve >= .999) { gl_FragColor = vec4(photo, 1.); return; }
  vec3 control = texture2D(uControl, uv).rgb;
  float terrain = control.r;
  float person = control.g;
  float p = uResolve;
  float displacement = (1. - smoothstep(.08, .48, p)) * .0012
    + abs(uVelocity) * .0008 * (1. - smoothstep(.65, .98, p));
  vec2 shift = vec2((control.b - .5) * displacement * terrain, 0.);
  vec3 drawing = texture2D(uDrawing, clamp(uv + shift, .001, .999)).rgb;
  float shade = smoothstep(.25, .76, p);
  float color = smoothstep(.44, .94, p);
  float personReveal = smoothstep(.66, .94, p);
  float localReveal = shade * (1. - .18 * person * (1. - personReveal));
  float luminance = dot(photo, vec3(.2126, .7152, .0722));
  vec3 paper = vec3(.953, .941, .906);
  vec3 tonal = mix(paper, vec3(.12, .19, .24), (1. - luminance) * .76);
  vec3 photographic = mix(tonal, photo, color);
  vec3 result = mix(drawing, photographic, localReveal);
  // An independent final pass removes every trace of paper/ink at the endpoint.
  result = mix(result, photo, smoothstep(.84, 1., p));
  gl_FragColor = vec4(result, 1.);
}`;

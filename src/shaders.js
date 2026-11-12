import { STAGES } from './progression.js';
const bounds = (name) => STAGES[name].map((value) => value.toFixed(3)).join(', ');

export const vertex = `
attribute vec2 aPosition;
varying vec2 vUv;
void main() {
  vUv = vec2(aPosition.x * .5 + .5, .5 - aPosition.y * .5);
  gl_Position = vec4(aPosition, 0., 1.);
}`;

// Stroke arrival controls pen travel. Independent layer opacity and saturation
// give the scene time to become a detailed sketch before color takes over.
export const fragment = `
precision mediump float;
varying vec2 vUv;
uniform sampler2D uInk0;
uniform sampler2D uTime0;
uniform sampler2D uInk1;
uniform sampler2D uTime1;
uniform sampler2D uInk2;
uniform sampler2D uTime2;
uniform vec2 uScale;
uniform vec2 uOffset;
uniform float uResolve;

vec3 addStrokes(vec3 ground, sampler2D inkTexture, sampler2D timeTexture,
               vec2 uv, float opacity, float saturation) {
  vec4 ink = texture2D(inkTexture, uv);
  float arrival = texture2D(timeTexture, uv).r * 1.1 - .1;
  float drawn = uResolve >= 1. ? 1. : smoothstep(arrival - .012, arrival + .012, uResolve);
  float luminance = dot(ink.rgb, vec3(.2126, .7152, .0722));
  vec3 color = mix(vec3(luminance), ink.rgb, saturation);
  return mix(ground, color, ink.a * drawn * opacity);
}
void main() {
  vec2 uv = vUv * uScale + uOffset;
  vec3 result = vec3(243. / 255., 240. / 255., 231. / 255.);
  float sketch = 1. - smoothstep(${bounds('sketchFade')}, uResolve);
  float broad = smoothstep(${bounds('broadOpacity')}, uResolve);
  float detail = smoothstep(${bounds('detailOpacity')}, uResolve);
  float saturation = smoothstep(${bounds('saturation')}, uResolve);
  result = addStrokes(result, uInk0, uTime0, uv, sketch, 0.);
  result = addStrokes(result, uInk1, uTime1, uv, broad, saturation);
  result = addStrokes(result, uInk2, uTime2, uv, detail, saturation);
  gl_FragColor = vec4(result, 1.);
}`;

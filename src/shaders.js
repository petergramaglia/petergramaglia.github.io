import { STAGES } from './progression.js';
const bounds = (name) => STAGES[name].map((value) => value.toFixed(3)).join(', ');

export const vertex = `
attribute vec2 aPosition;
varying vec2 vUv;
void main() {
  vUv = vec2(aPosition.x * .5 + .5, .5 - aPosition.y * .5);
  gl_Position = vec4(aPosition, 0., 1.);
}`;

// Atlas arrival controls both pen travel and local pigment maturity.
// Regional schedules, rather than a global fade, order the painted forms.
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
               vec2 uv, float opacity, bool colored) {
  vec4 ink = texture2D(inkTexture, uv);
  float arrival = texture2D(timeTexture, uv).r * 1.1 - .1;
  float age = uResolve - arrival;
  float drawn = uResolve >= 1. ? 1. : (colored
    ? smoothstep(${bounds('strokeReveal')}, age)
    : smoothstep(${bounds('sketchReveal')}, age));
  float saturation = colored ? smoothstep(${bounds('strokePigment')}, age) : 0.;
  float maturity = colored ? .55 + .45 * smoothstep(${bounds('strokeOpacity')}, age) : 1.;
  if (uResolve >= 1. && colored) { saturation = 1.; maturity = 1.; }
  float luminance = dot(ink.rgb, vec3(.2126, .7152, .0722));
  vec3 color = mix(vec3(luminance), ink.rgb, saturation);
  return mix(ground, color, ink.a * drawn * opacity * maturity);
}
void main() {
  vec2 uv = vUv * uScale + uOffset;
  vec3 result = vec3(243. / 255., 240. / 255., 231. / 255.);
  float sketch = 1. - smoothstep(${bounds('sketchFade')}, uResolve);
  result = addStrokes(result, uInk0, uTime0, uv, sketch, false);
  result = addStrokes(result, uInk1, uTime1, uv, 1., true);
  result = addStrokes(result, uInk2, uTime2, uv, 1., true);
  gl_FragColor = vec4(result, 1.);
}`;

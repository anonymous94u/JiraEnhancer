# Laplace-domain confidence-gap diagnostic

This document provides the full derivation supporting Section 3.6.4 of the Jira Enhancer manuscript. Equations retain their manuscript numbers (41–47). The [original LaTeX subsection](laplace_convergence_original.tex) is retained for traceability.

## Scope and assumptions

The executable refinement workflow proceeds in discrete attempts and stops at the configured confidence/validation gate or attempt horizon. The continuous-time interpolation $\ell(t)$ of the logged confidence gap is an idealized diagnostic of the internal metric. The stability result below assumes a constant $\kappa>0$ and finite initial lag. It is distinct from a convergence guarantee for the learned prompt policy or a guarantee of semantic requirement correctness.

## Dynamics and Laplace transform

Let the interpolated lag satisfy

$$
\frac{d\ell(t)}{dt}=-\kappa\ell(t)+d_{\ell}(t). \tag{41}
$$

Here $d_{\ell}(t)$ represents disturbance from evidence gaps, conflicting context, or reviewer feedback. Write $s_L$ for the Laplace variable, $\Lambda_{\ell}(s_L)=\mathcal{L}\{\ell(t)\}$, and $D_{\ell}(s_L)=\mathcal{L}\{d_{\ell}(t)\}$. Applying the derivative transform yields

$$
s_L\Lambda_{\ell}(s_L)-\ell(0)=-\kappa\Lambda_{\ell}(s_L)+D_{\ell}(s_L). \tag{42}
$$

Rearranging gives

$$
\Lambda_{\ell}(s_L)=\frac{\ell(0)+D_{\ell}(s_L)}{s_L+\kappa}. \tag{43}
$$

For zero disturbance, $D_{\ell}(s_L)=0$, so

$$
\Lambda_{\ell}(s_L)=\frac{\ell(0)}{s_L+\kappa}. \tag{44}
$$

The pole lies at $s_L=-\kappa<0$. The inverse transform is $\ell(t)=\ell(0)e^{-\kappa t}$, and the final value theorem gives

$$
\lim_{t\to\infty}\ell(t)=\lim_{s_L\to0}s_L\Lambda_{\ell}(s_L)=0. \tag{45}
$$

## Bounded disturbance

For $|d_{\ell}(t)|\le d_{\max}$, the variation-of-constants solution is

$$
\ell(t)=\ell(0)e^{-\kappa t}+\int_0^t e^{-\kappa(t-u)}d_{\ell}(u)\,du.
$$

Consequently,

$$
|\ell(t)|\le |\ell(0)|e^{-\kappa t}+\frac{d_{\max}}{\kappa}(1-e^{-\kappa t}),
\qquad
\limsup_{t\to\infty}|\ell(t)|\le\frac{d_{\max}}{\kappa}.
$$

This is an asymptotic bound; a bounded persistent disturbance need not produce a zero limit or a constant steady state.

## Rate diagnostic and implementation correspondence

The original subsection included the following rate expression:

$$
\kappa=\max\left(\frac{n}{\sum\delta},\epsilon\right). \tag{46}
$$

Equation (46) is retained as part of the archived derivation, not as a specification of the executable estimator. The original excerpt does not define $n$ and $\delta$; applying a maximum after division also does not guard a zero denominator. Neither this expression nor an empirical rate estimate is needed for the stability calculation above, which assumes constant positive $\kappa$.

The released code's [`_loss_metrics`](../src/jira_enhancer/rl/service.py) computes the per-attempt diagnostic

$$
\widehat{\kappa}_t=\max\left(0,\log\frac{\ell_{\mathrm{before}}+10^{-6}}{\ell_{\mathrm{after}}+10^{-6}}\right).
$$

It records this quantity with the before/after confidence gaps and normalized losses. This diagnostic is distinct from the constant model parameter assumed in the continuous-time derivation. The implemented estimator and refinement algorithm are unchanged.

## Limit retained in the manuscript

Under the zero-disturbance, constant-positive-gain assumptions above, the retained Final Value Theorem statement is

$$
\lim_{t\to\infty}\ell(t)=\lim_{s_L\to0}s_L\Lambda_{\ell}(s_L)=0. \tag{47}
$$

The result describes the idealized internal confidence-gap model. Human review, content validation, and transaction controls remain separate parts of the executable workflow.

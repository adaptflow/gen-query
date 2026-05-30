import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import styles from './index.module.css';

const features = [
  {
    title: 'Agentic pipeline',
    description: 'Inspector, Ranker, Planner, and Executor stages keep generation explainable and customizable.',
  },
  {
    title: 'Sync and async APIs',
    description: 'Use GenQuery in scripts, notebooks, workers, or asyncio web services such as FastAPI.',
  },
  {
    title: 'Security-first SQL execution',
    description: 'Read-only validation, row limits, statement timeouts, and Row-Level Security support are built in.',
  },
  {
    title: 'Streaming Polars results',
    description: 'Consume large final result sets as Polars DataFrame batches without loading everything into memory.',
  },
];

function HomepageHeader() {
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">GenQuery</Heading>
        <p className="hero__subtitle">Agentic Natural Language to SQL for Python</p>
        <div className={styles.buttons}>
          <Link className="button button--secondary button--lg" to="/docs/intro">
            Get Started
          </Link>
          <Link className="button button--outline button--secondary button--lg" to="/docs/getting-started/quick-start">
            Quick Start
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home() {
  return (
    <Layout
      title="GenQuery"
      description="Agentic Natural Language to SQL generation and execution for Python">
      <HomepageHeader />
      <main className="container margin-vert--xl">
        <section className="features">
          {features.map((feature) => (
            <article className="featureCard" key={feature.title}>
              <Heading as="h3">{feature.title}</Heading>
              <p>{feature.description}</p>
            </article>
          ))}
        </section>
        <section className="margin-top--xl">
          <Heading as="h2">Minimal example</Heading>
          <pre>
            <code>{`from genquery import GenQuery
from genquery.adapters.openai_adapter import OpenAIAdapter

llm = OpenAIAdapter(api_key="sk-...", model="gpt-5.5")
gq = GenQuery(
    llm=llm,
    connection_string="postgresql://user:pass@localhost:5432/mydb",
    schema="public",
)

df = gq.run("Show top 5 customers by total order amount this year")
print(df)`}</code>
          </pre>
        </section>
      </main>
    </Layout>
  );
}

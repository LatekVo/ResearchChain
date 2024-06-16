"use client";
import React from "react";
import Header from "../components/Header";
import { useQuery } from "react-query";
import HistoryCard from "../components/HistoryCard"
import { data } from "./crawlHistoryMock";

const CrawlHistory = () => {
  // const { data, isLoading, isError } = useQuery<CrawlHistoryItem[], Error>(
  //   "crawlHistory",
  //   async () => {
  //     const response = await fetch("http://127.0.0.1:8000/crawl");
  //     if (!response.ok) {
  //       throw new Error("Failed to fetch crawl history");
  //     }
  //     return response.json();
  //   }
  // );

  const isLoading = false;
  const isError = false;

  if (isLoading) {
    return (
      <div className="h-full w-full">
        <Header></Header>
        <div className="text-center">Loading...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="h-screen w-screen">
        <Header></Header>
        <div className="text-center">Fetching data</div>
      </div>
    );
  }

  if (!data || data.task.length === 0) {
    return (
      <div className="h-screen w-screen">
        <Header></Header>
        <div className="text-center">There is no crawler history</div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex-col">
      <Header></Header>
      <div className="h-4/5 w-full flex-col items-center justify-center">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-5 gap-4 p-4">
          {data.task.map((item) => (
            <HistoryCard key={item.uuid} item={item}></HistoryCard>

          ))}
        </div>
      </div>
    </div>
  );
};

export default CrawlHistory;

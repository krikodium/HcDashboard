import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Navigation from './Navigation';

const Layout = () => {
  return (
    <div className="min-h-screen theme-background">
      <Header />
      <div className="flex">
        <Navigation />
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
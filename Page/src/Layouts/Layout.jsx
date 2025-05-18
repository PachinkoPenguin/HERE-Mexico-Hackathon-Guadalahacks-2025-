import React from 'react';

const Layout = ({ children }) => {
  return (
    <div className="w-full min-h-screen bg-white flex flex-col items-center justify-start relative">

      <div className="w-full flex items-start justify-center z-10">
        <div className="w-[100%] h-[70vh] flex flex-col">
          {children}
        </div>
      </div>
    </div>
  );
};

export default Layout;

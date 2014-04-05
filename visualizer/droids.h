#ifndef DROIDS_H
#define DROIDS_H

#include <QObject>
#include <QThread>
#include "igame.h"
#include "animsequence.h"
#include <map>
#include <string>
#include <list>

// The Codegen's Parser
#include "parser/parser.h"
#include "parser/structures.h"

using namespace std;

namespace visualizer
{
    class Droids: public QThread, public AnimSequence, public IGame
    {
        Q_OBJECT;
        Q_INTERFACES( visualizer::IGame );

        private:
            static const int IDLE = 6;

			enum DROID_TYPE
			{
				DROID_CLAW = 0,
				DROID_ARCHER,
				DROID_REPAIRER,
				DROID_HACKER,
				DROID_TURRET,
				DROID_WALL,
				DROID_TERMINATOR,
				DROID_HANGAR
			};


        public: 
            Droids();
            ~Droids();

            PluginInfo getPluginInfo();
            void loadGamelog( std::string gamelog );

            void run();
            void setup();
            void destroy();

            void preDraw();
            void postDraw();

            void addCurrentBoard();
    
            map<string, int> programs;
            
            list<int> getSelectedUnits();
		private:
			void RenderGrid() const;

            void PrepareUnits(const int& frameNum,Frame& turn) const;

            void PrepareStructures(const int& frameNum, Frame& turn) const;

        private:
            parser::Game *m_game;  // The Game Object from parser/structures.h that is generated by the Codegen
			int m_mapWidth;
			int m_mapHeight;
            bool m_suicide;

			static const unsigned int GRID_OFFSET = 1;
    }; 

} // visualizer

#endif // DROIDS_H

import React, { useState, useCallback, memo } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Divider,
  ListItemButton,
  Chip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Chat as ChatIcon,
  Settings as SettingsIcon,
  LibraryBooks as KnowledgeIcon,
  AccountCircle,
  Logout as LogoutIcon,
  People as PeopleIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const drawerWidth = 240;

interface LayoutProps {
  children: React.ReactNode;
}

interface MenuItemType {
  text: string;
  icon: React.ReactNode;
  path: string;
}

interface DrawerContentProps {
  menuItems: MenuItemType[];
  location: ReturnType<typeof useLocation>;
  onNavigate: (path: string) => void;
}

const DrawerContent: React.FC<DrawerContentProps> = memo(({ menuItems, location, onNavigate }) => {
  const handleMenuItemClick = useCallback(
    (path: string) => {
      onNavigate(path);
    },
    [onNavigate],
  );

  return (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          チャットボットシステム
        </Typography>
      </Toolbar>
      <List>
        {menuItems.map(item => (
          <ListItem
            button
            key={item.text}
            selected={location.pathname === item.path}
            onClick={() => handleMenuItemClick(item.path)}
            sx={{
              '&.Mui-selected': {
                backgroundColor: 'rgba(25, 118, 210, 0.08)',
              },
              '&.Mui-selected:hover': {
                backgroundColor: 'rgba(25, 118, 210, 0.12)',
              },
            }}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </div>
  );
});

DrawerContent.displayName = 'DrawerContent';

interface AppBarContentProps {
  menuItems: MenuItemType[];
  location: ReturnType<typeof useLocation>;
  onProfileMenuOpen: (event: React.MouseEvent<HTMLElement>) => void;
  onDrawerToggle: () => void;
  anchorEl: HTMLElement | null;
  onProfileMenuClose: () => void;
}

const AppBarContent: React.FC<AppBarContentProps> = memo(
  ({ menuItems, location, onProfileMenuOpen, onDrawerToggle, anchorEl, onProfileMenuClose }) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const currentTitle =
      menuItems.find(item => item.path === location.pathname)?.text ?? 'チャットボットシステム';

    const handleLogout = async () => {
      await logout();
      navigate('/login');
      onProfileMenuClose();
    };

    return (
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={onDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {currentTitle}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mr: 2 }}>
            <Chip
              label={user?.role === 'admin' ? '管理者' : 'ユーザー'}
              size="small"
              color={user?.role === 'admin' ? 'secondary' : 'default'}
              sx={{ color: 'white', borderColor: 'white' }}
            />
            <Typography variant="body2" sx={{ display: { xs: 'none', md: 'block' } }}>
              {user?.username}
            </Typography>
          </Box>
          <IconButton
            size="large"
            aria-label="account of current user"
            aria-controls="menu-appbar"
            aria-haspopup="true"
            onClick={onProfileMenuOpen}
            color="inherit"
          >
            <AccountCircle />
          </IconButton>
          <Menu
            id="menu-appbar"
            anchorEl={anchorEl}
            anchorOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            keepMounted
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            open={Boolean(anchorEl)}
            onClose={onProfileMenuClose}
          >
            <MenuItem disabled>
              <Typography variant="body2" color="text.secondary">
                {user?.email}
              </Typography>
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout}>
              <ListItemIcon>
                <LogoutIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>ログアウト</ListItemText>
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>
    );
  },
);

AppBarContent.displayName = 'AppBarContent';

interface NavigationDrawerProps {
  mobileOpen: boolean;
  onDrawerToggle: () => void;
  menuItems: MenuItemType[];
  location: ReturnType<typeof useLocation>;
  onNavigate: (path: string) => void;
}

const NavigationDrawer: React.FC<NavigationDrawerProps> = memo(
  ({ mobileOpen, onDrawerToggle, menuItems, location, onNavigate }) => {
    return (
      <Box component="nav" sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}>
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={onDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          <DrawerContent menuItems={menuItems} location={location} onNavigate={onNavigate} />
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          <DrawerContent menuItems={menuItems} location={location} onNavigate={onNavigate} />
        </Drawer>
      </Box>
    );
  },
);

NavigationDrawer.displayName = 'NavigationDrawer';

interface MainContentProps {
  children: React.ReactNode;
}

const MainContent: React.FC<MainContentProps> = memo(({ children }) => {
  return (
    <Box
      component="main"
      sx={{
        flexGrow: 1,
        p: 3,
        width: { sm: `calc(100% - ${drawerWidth}px)` },
      }}
    >
      <Toolbar /> {/* AppBarのスペース確保 */}
      {children}
    </Box>
  );
});

MainContent.displayName = 'MainContent';

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const navigate = useNavigate();
  const location = useLocation();

  const handleDrawerToggle = useCallback(() => {
    setMobileOpen(!mobileOpen);
  }, [mobileOpen]);

  const handleProfileMenuOpen = useCallback((event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  }, []);

  const handleProfileMenuClose = useCallback(() => {
    setAnchorEl(null);
  }, []);

  const handleNavigation = useCallback(
    (path: string) => {
      navigate(path);
    },
    [navigate],
  );

  const { isAdmin } = useAuth();

  const menuItems: MenuItemType[] = [
    { text: 'チャットボット', icon: <ChatIcon />, path: '/chat' },
    ...(isAdmin ? [
      { text: 'LLM設定', icon: <SettingsIcon />, path: '/llm-config' },
      { text: 'ナレッジ設定', icon: <KnowledgeIcon />, path: '/knowledge' },
      { text: 'ユーザー管理', icon: <PeopleIcon />, path: '/users' }
    ] : []),
  ];

  return (
    <Box sx={{ display: 'flex', height: '90vh' }}>
      <AppBarContent
        menuItems={menuItems}
        location={location}
        onProfileMenuOpen={handleProfileMenuOpen}
        onDrawerToggle={handleDrawerToggle}
        anchorEl={anchorEl}
        onProfileMenuClose={handleProfileMenuClose}
      />
      <NavigationDrawer
        mobileOpen={mobileOpen}
        onDrawerToggle={handleDrawerToggle}
        menuItems={menuItems}
        location={location}
        onNavigate={handleNavigation}
      />
      <MainContent>{children}</MainContent>
    </Box>
  );
};

export default Layout;

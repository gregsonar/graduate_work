import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const NotificationAdmin = () => {
  // States for instant message form
  const [instantMessage, setInstantMessage] = useState({
    body: '',
    subject: '',
    message_type: 'email',
    user_id: ''
  });

  // State for new user form
  const [newUserMessage, setNewUserMessage] = useState({
    user_id: ''
  });

  // State for global message form
  const [globalMessage, setGlobalMessage] = useState({
    body: ''
  });

  // States for rule form
  const [rule, setRule] = useState({
    name: '',
    template: '',
    subject: '',
    timetable: {
      min: 0,
      h: 0,
      day: 1,
      month: 1,
      week_day: 0
    }
  });

  // State for response message
  const [response, setResponse] = useState(null);

  // Function to handle instant message submission
  const handleInstantMessage = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/instant_message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(instantMessage),
      });
      const data = await res.json();
      setResponse({ success: res.ok, message: res.ok ? 'Message sent successfully' : data.message });
    } catch (error) {
      setResponse({ success: false, message: 'Error sending message' });
    }
  };

  // Function to handle new user message submission
  const handleNewUser = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/new-user', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newUserMessage),
      });
      const data = await res.json();
      setResponse({ success: res.ok, message: res.ok ? 'Welcome message sent' : data.message });
    } catch (error) {
      setResponse({ success: false, message: 'Error sending welcome message' });
    }
  };

  // Function to handle global message submission
  const handleGlobalMessage = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/to-all', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(globalMessage),
      });
      const data = await res.json();
      setResponse({ success: res.ok, message: res.ok ? 'Global message sent' : data.message });
    } catch (error) {
      setResponse({ success: false, message: 'Error sending global message' });
    }
  };

  // Function to handle rule submission
  const handleRule = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/rule', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(rule),
      });
      const data = await res.json();
      setResponse({ success: res.ok, message: res.ok ? 'Rule created successfully' : data.message });
    } catch (error) {
      setResponse({ success: false, message: 'Error creating rule' });
    }
  };

  return (
    <div className="container mx-auto p-4">
      <Card className="mb-4">
        <CardHeader>
          <CardTitle>Notification Admin Interface</CardTitle>
        </CardHeader>
      </Card>

      {response && (
        <Alert className={`mb-4 ${response.success ? 'bg-green-50' : 'bg-red-50'}`}>
          <AlertDescription>{response.message}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="instant" className="space-y-4">
        <TabsList>
          <TabsTrigger value="instant">Instant Message</TabsTrigger>
          <TabsTrigger value="welcome">Welcome Message</TabsTrigger>
          <TabsTrigger value="global">Global Message</TabsTrigger>
          <TabsTrigger value="rule">Rule</TabsTrigger>
        </TabsList>

        <TabsContent value="instant">
          <Card>
            <CardHeader>
              <CardTitle>Send Instant Message</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleInstantMessage} className="space-y-4">
                <div className="grid gap-4">
                  <Input
                    placeholder="User ID"
                    value={instantMessage.user_id}
                    onChange={(e) => setInstantMessage({...instantMessage, user_id: e.target.value})}
                  />
                  <Input
                    placeholder="Subject"
                    value={instantMessage.subject}
                    onChange={(e) => setInstantMessage({...instantMessage, subject: e.target.value})}
                  />
                  <Textarea
                    placeholder="Message body"
                    value={instantMessage.body}
                    onChange={(e) => setInstantMessage({...instantMessage, body: e.target.value})}
                  />
                  <Select
                    value={instantMessage.message_type}
                    onValueChange={(value) => setInstantMessage({...instantMessage, message_type: value})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Message type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="email">Email</SelectItem>
                      <SelectItem value="websocket">WebSocket</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button type="submit">Send Message</Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="welcome">
          <Card>
            <CardHeader>
              <CardTitle>Send Welcome Message</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleNewUser} className="space-y-4">
                <Input
                  placeholder="User ID"
                  value={newUserMessage.user_id}
                  onChange={(e) => setNewUserMessage({...newUserMessage, user_id: e.target.value})}
                />
                <Button type="submit">Send Welcome Message</Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="global">
          <Card>
            <CardHeader>
              <CardTitle>Send Global Message</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleGlobalMessage} className="space-y-4">
                <Textarea
                  placeholder="Message body"
                  value={globalMessage.body}
                  onChange={(e) => setGlobalMessage({...globalMessage, body: e.target.value})}
                />
                <Button type="submit">Send Global Message</Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="rule">
          <Card>
            <CardHeader>
              <CardTitle>Create Notification Rule</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleRule} className="space-y-4">
                <div className="grid gap-4">
                  <Input
                    placeholder="Rule name"
                    value={rule.name}
                    onChange={(e) => setRule({...rule, name: e.target.value})}
                  />
                  <Input
                    placeholder="Subject"
                    value={rule.subject}
                    onChange={(e) => setRule({...rule, subject: e.target.value})}
                  />
                  <Textarea
                    placeholder="Template"
                    value={rule.template}
                    onChange={(e) => setRule({...rule, template: e.target.value})}
                  />
                  <div className="grid grid-cols-5 gap-2">
                    <Input
                      type="number"
                      min="0"
                      max="59"
                      placeholder="Min"
                      value={rule.timetable.min}
                      onChange={(e) => setRule({
                        ...rule,
                        timetable: {...rule.timetable, min: parseInt(e.target.value)}
                      })}
                    />
                    <Input
                      type="number"
                      min="0"
                      max="23"
                      placeholder="Hour"
                      value={rule.timetable.h}
                      onChange={(e) => setRule({
                        ...rule,
                        timetable: {...rule.timetable, h: parseInt(e.target.value)}
                      })}
                    />
                    <Input
                      type="number"
                      min="1"
                      max="31"
                      placeholder="Day"
                      value={rule.timetable.day}
                      onChange={(e) => setRule({
                        ...rule,
                        timetable: {...rule.timetable, day: parseInt(e.target.value)}
                      })}
                    />
                    <Input
                      type="number"
                      min="1"
                      max="12"
                      placeholder="Month"
                      value={rule.timetable.month}
                      onChange={(e) => setRule({
                        ...rule,
                        timetable: {...rule.timetable, month: parseInt(e.target.value)}
                      })}
                    />
                    <Input
                      type="number"
                      min="0"
                      max="6"
                      placeholder="Week day"
                      value={rule.timetable.week_day}
                      onChange={(e) => setRule({
                        ...rule,
                        timetable: {...rule.timetable, week_day: parseInt(e.target.value)}
                      })}
                    />
                  </div>
                </div>
                <Button type="submit">Create Rule</Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default NotificationAdmin;